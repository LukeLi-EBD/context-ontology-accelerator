"""C2 quota tests: provider codes, simple counters, restart, over-limit, off, full.

Pure unit tests: the metadata store is an in-memory fake that keeps the exact
SQL surface SimpleQuota uses. Run from the repo root with the packages on
``PYTHONPATH`` (see doc/coa-x/07-研发台账.md):

  python -m pytest packages/platform-core/tests/test_c2_quota.py \
    --import-mode=importlib -p no:cacheprovider
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, "/app/src")
sys.path.insert(0, "../src")
sys.path.insert(0, "/hostsrc")  # mounted worktree wins over the image copy
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import platform_core.api as api_module
from platform_core.adapters.quota_full import FullQuota
from platform_core.adapters.quota_off import OffQuota
from platform_core.adapters.quota_simple import SimpleQuota
from platform_core.config import ExtractionConfig, ExtractionRule, QuotaConfig, load_config
from platform_core.errors import EXIT_CONFIG, PlatformError, PortError
from platform_core.extraction import ExtractionService
from platform_core.quota_gate import QuotaAwareLlm, build_quota

BASE = {"database": {"url": "postgresql://platform:platform_dev@postgres:5432/platform"}}
DAY = date(2026, 11, 6)


def load(overrides: dict, environ: dict | None = None):
    doc = dict(BASE)
    for key, value in overrides.items():
        if isinstance(value, dict):
            doc.setdefault(key, {}).update(value)
        else:
            doc[key] = value
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
        yaml.safe_dump(doc, handle)
        path = handle.name
    try:
        return load_config(path, environ=environ or {})
    finally:
        Path(path).unlink(missing_ok=True)


class FakeStore:
    """In-memory stand-in for platform.quota_usage (same query/execute surface)."""

    def __init__(self) -> None:
        self.rows: dict[tuple[date, str], dict] = {}
        self.calls = 0

    def query(self, sql: str, params: tuple | list = ()) -> list[dict]:
        self.calls += 1
        if "FROM platform.quota_usage" not in sql:
            raise AssertionError(f"unexpected query: {sql.strip()[:80]}")
        day, scope = params
        row = self.rows.get((day, scope))
        return [dict(row)] if row else []

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        self.calls += 1
        if "INSERT INTO platform.quota_usage" not in sql:
            raise AssertionError(f"unexpected execute: {sql.strip()[:80]}")
        day, scope, tokens, cost = params
        row = self.rows.setdefault(
            (day, scope), {"tokens": 0, "requests": 0, "cost_units": 0.0}
        )
        row["tokens"] += int(tokens)
        row["requests"] += 1
        row["cost_units"] += float(cost)
        return 1


class FakeLlm:
    def __init__(self, usage: dict | None = None) -> None:
        self.calls = 0
        self.last_usage = usage

    def configured(self) -> bool:
        return True

    def manifest(self):
        return SimpleNamespace(notes={}, provider="fake")

    def close(self) -> None:
        pass

    def complete_json(self, _system: str, _user: str) -> dict:
        self.calls += 1
        return {"triples": []}


def simple_quota(**kwargs) -> tuple[SimpleQuota, FakeStore]:
    store = FakeStore()
    quota = SimpleQuota(QuotaConfig(provider="simple", **kwargs), store, clock=lambda: DAY)
    return quota, store


class _ExtractMeta:
    """Metadata fake for one extraction run (rules + failed LLM attempt)."""

    def __init__(self) -> None:
        self.inserted = 0
        self.progress_writes = 0

    def query(self, sql: str, params: tuple | list = ()) -> list[dict]:
        if "FROM platform.document WHERE" in sql:
            return [{"document_id": params[0]}]
        if "FROM platform.document_chunk" in sql:
            return [{"chunk_id": "chunk-1", "seq": 1, "text": "Alice位于China"}]
        if "FROM platform.extraction_progress" in sql:
            return []
        raise AssertionError(f"unexpected query: {sql.strip()[:80]}")

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        if "INSERT INTO platform.extraction_candidate" in sql:
            self.inserted += 1
            return 1
        if "INSERT INTO platform.extraction_progress" in sql:
            self.progress_writes += 1
            return 1
        raise AssertionError(f"unexpected execute: {sql.strip()[:80]}")


RULES = [
    ExtractionRule(
        name="located_in",
        pattern=r"(?P<subject>[A-Za-z0-9]{2,20})位于(?P<object>[A-Za-z0-9]{2,20})",
        predicate="urn:platform:rel:locatedIn",
        subject="urn:platform:entity:{subject}",
        object="urn:platform:entity:{object}",
    )
]


class ProviderCodeTests(unittest.TestCase):
    def test_default_is_off(self):
        bundle = load({})
        self.assertEqual(bundle.config.quota.provider, "off")

    def test_unknown_provider_is_invalid(self):
        with self.assertRaises(PlatformError) as ctx:
            load({"quota": {"provider": "nope"}})
        err = ctx.exception
        self.assertEqual(err.code, "E_PROVIDER_INVALID")
        self.assertEqual(err.key, "quota.provider")
        self.assertEqual(err.exit_code, EXIT_CONFIG)
        self.assertIn("known values: off, simple, full", err.detail)

    def test_full_is_known_but_not_implemented(self):
        with self.assertRaises(PlatformError) as ctx:
            load({"quota": {"provider": "full"}})
        err = ctx.exception
        self.assertEqual(err.code, "E_PROVIDER_NOT_IMPLEMENTED")
        self.assertEqual(err.key, "quota.provider")
        self.assertEqual(err.exit_code, EXIT_CONFIG)
        self.assertIn("C2-2", err.detail)

    def test_off_and_simple_load(self):
        self.assertEqual(load({"quota": {"provider": "off"}}).config.quota.provider, "off")
        self.assertEqual(
            load({"quota": {"provider": "simple"}}).config.quota.provider, "simple"
        )

    def test_simple_zero_limits_warns(self):
        bundle = load({"quota": {"provider": "simple"}})
        self.assertTrue(any("counted but nothing is enforced" in item for item in bundle.warnings))

    def test_build_quota_three_values(self):
        store = FakeStore()
        self.assertIsInstance(
            build_quota(QuotaConfig(provider="off"), store), OffQuota
        )
        self.assertIsInstance(
            build_quota(QuotaConfig(provider="simple"), store), SimpleQuota
        )
        # load_config blocks full, but the assembly branch exists (canvas pattern).
        self.assertIsInstance(build_quota(QuotaConfig(provider="full"), store), FullQuota)


class SimpleQuotaTests(unittest.TestCase):
    def test_off_allows_and_never_counts(self):
        # OffQuota has no metadata dependency at all: off cannot read or write.
        quota = OffQuota(QuotaConfig(provider="off", daily_token_limit=1))
        decision = quota.check("llm", 1000)
        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.reason)
        quota.record("llm", 1000)
        status = quota.status("llm")
        self.assertEqual(status["provider"], "off")
        self.assertFalse(status["counted"])
        self.assertEqual(status["tokens"]["used"], 0)
        self.assertEqual(status["tokens"]["limit"], None)

    def test_simple_counts_tokens_and_requests(self):
        quota, _store = simple_quota(daily_token_limit=100, daily_request_limit=10)
        quota.record("llm", 40, cost=0.0)
        status = quota.status("llm")
        self.assertEqual(status["tokens"]["used"], 40)
        self.assertEqual(status["tokens"]["remaining"], 60)
        self.assertEqual(status["requests"]["used"], 1)
        self.assertTrue(status["counted"])
        self.assertEqual(status["day"], "2026-11-06")

    def test_token_limit_degrades_with_code(self):
        quota, _store = simple_quota(daily_token_limit=100, on_exceed="degrade")
        quota.record("llm", 40)
        decision = quota.check("llm", 61)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "E_QUOTA_EXCEEDED")
        self.assertEqual(decision.action, "degrade")
        self.assertEqual(decision.remaining_tokens, 60)

    def test_request_limit(self):
        quota, _store = simple_quota(daily_request_limit=2)
        quota.record("llm", 0)
        quota.record("llm", 0)
        decision = quota.check("llm", 1)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "E_QUOTA_EXCEEDED")
        self.assertEqual(decision.used_requests, 2)

    def test_reject_policy_is_reported(self):
        quota, _store = simple_quota(daily_token_limit=10, on_exceed="reject")
        quota.record("llm", 10)
        decision = quota.check("llm", 5)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "reject")

    def test_zero_limit_means_unlimited_but_counts(self):
        quota, _store = simple_quota()
        quota.record("llm", 999)
        decision = quota.check("llm", 1000)
        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.limit_tokens)
        self.assertIsNone(decision.remaining_tokens)
        self.assertEqual(quota.status("llm")["tokens"]["used"], 999)

    def test_counters_survive_restart(self):
        quota, store = simple_quota(daily_token_limit=1000)
        quota.record("llm", 25)
        quota.record("llm", 15)
        # "Restart": a brand-new instance over the same persistent store.
        revived = SimpleQuota(quota._config, store, clock=lambda: DAY)
        status = revived.status("llm")
        self.assertEqual(status["tokens"]["used"], 40)
        self.assertEqual(status["requests"]["used"], 2)
        self.assertEqual(status["tokens"]["remaining"], 960)

    def test_scope_is_part_of_the_key(self):
        quota, _store = simple_quota(daily_token_limit=100)
        quota.record("llm", 10)
        quota.record("other", 20)
        self.assertEqual(quota.status("llm")["tokens"]["used"], 10)
        self.assertEqual(quota.status("other")["tokens"]["used"], 20)

    def test_empty_scope_is_rejected(self):
        quota, _store = simple_quota()
        with self.assertRaises(PortError) as ctx:
            quota.check("   ", 1)
        self.assertEqual(ctx.exception.provider_code, "E_QUOTA_SCOPE_INVALID")


class FullQuotaSkeletonTests(unittest.TestCase):
    def test_every_method_raises_not_implemented(self):
        quota = FullQuota()
        self.assertEqual(quota.manifest().notes["status"], "not_implemented")
        for call in (
            lambda: quota.check("llm", 1),
            lambda: quota.record("llm", 1),
            lambda: quota.status("llm"),
        ):
            with self.assertRaises(PortError) as ctx:
                call()
            self.assertEqual(ctx.exception.provider_code, "E_PROVIDER_NOT_IMPLEMENTED")
            self.assertEqual(ctx.exception.provider, "full")


class LlmGateTests(unittest.TestCase):
    def test_over_limit_skips_the_llm_call(self):
        quota, store = simple_quota(daily_token_limit=5)
        inner = FakeLlm()
        gate = QuotaAwareLlm(inner, quota, scope="llm", chars_per_token=4)
        with self.assertRaises(PortError) as ctx:
            gate.complete_json("sys" * 100, "user" * 100)
        err = ctx.exception
        self.assertEqual(err.provider_code, "E_QUOTA_EXCEEDED")
        self.assertEqual(err.code, "ResourceExhausted")
        self.assertEqual(err.details["action"], "degrade")
        self.assertEqual(inner.calls, 0)  # LLM was skipped
        self.assertEqual(store.rows, {})  # nothing recorded for a skipped call

    def test_reject_policy_raises_policy_rejected(self):
        quota, _store = simple_quota(daily_token_limit=5, on_exceed="reject")
        gate = QuotaAwareLlm(FakeLlm(), quota, scope="llm", chars_per_token=4)
        with self.assertRaises(PortError) as ctx:
            gate.complete_json("x" * 100, "y")
        self.assertEqual(ctx.exception.provider_code, "E_QUOTA_EXCEEDED")
        self.assertEqual(ctx.exception.code, "PolicyRejected")

    def test_success_records_reported_usage(self):
        quota, store = simple_quota(daily_token_limit=1000)
        inner = FakeLlm(usage={"prompt_tokens": 30, "completion_tokens": 10})
        gate = QuotaAwareLlm(inner, quota, scope="llm", chars_per_token=4)
        gate.complete_json("short", "short")
        self.assertEqual(inner.calls, 1)
        self.assertEqual(store.rows[(DAY, "llm")]["tokens"], 40)
        self.assertEqual(store.rows[(DAY, "llm")]["requests"], 1)

    def test_degrade_path_keeps_rules_result_readable(self):
        quota, _store = simple_quota(daily_token_limit=5)
        meta = _ExtractMeta()
        llm = QuotaAwareLlm(FakeLlm(), quota, scope="llm", chars_per_token=4)
        service = ExtractionService(
            ExtractionConfig(enabled=True, rules=RULES), meta, object(), llm
        )
        result = service.extract_document("doc-1", mode="auto")
        self.assertTrue(result["degraded"])
        self.assertIn("E_QUOTA_EXCEEDED", result["reasons"])
        self.assertGreaterEqual(result["rulesMatched"], 1)
        self.assertGreaterEqual(result["inserted"], 1)  # still readable/useful
        self.assertIsNone(result["llm"])
        self.assertEqual(result["chunks"], 1)


class QuotaRouteTests(unittest.TestCase):
    def _client(self, provider: str, quota) -> TestClient:
        bundle = load({"quota": {"provider": provider}})
        runtime = SimpleNamespace(bundle=bundle, config=bundle.config, quota=quota, metadata=None)
        app = api_module.create_app(runtime, [])
        api_module.g7_register(app, runtime)
        return TestClient(app)

    def test_status_route_simple(self):
        quota, _store = simple_quota(daily_token_limit=100, daily_request_limit=5)
        quota.record("global", 20)
        client = self._client("simple", quota)
        self.assertEqual(client.get("/healthz").status_code, 200)  # existing route intact
        response = client.get("/quota/status", params={"scope": "global"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["provider"], "simple")
        self.assertEqual(body["tokens"]["used"], 20)
        self.assertEqual(body["tokens"]["limit"], 100)
        self.assertEqual(body["requests"]["used"], 1)

    def test_status_route_off(self):
        client = self._client("off", OffQuota(QuotaConfig(provider="off")))
        body = client.get("/quota/status").json()
        self.assertEqual(body["provider"], "off")
        self.assertFalse(body["counted"])

    def test_status_route_full_is_400(self):
        client = self._client("off", FullQuota())
        response = client.get("/quota/status")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_PROVIDER_NOT_IMPLEMENTED"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
