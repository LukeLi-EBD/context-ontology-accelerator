"""The local bridge must not drop the namespace uuid it already has.

`/namespaces/{namespaceId}/ontologies/{ontologyId}/import` and `.../publish`
carry the namespace in the path. The bridge used to forward only the ontology
id, so `platform.ontology_version.namespace_id` stayed NULL end to end even
after the kernel learned to store it (V52). These tests pin the forwarding.
"""

import asyncio
import importlib.util
import json
import sys
import unittest
from pathlib import Path

BRIDGE_PATH = (
    Path(__file__).resolve().parents[3] / "doc" / "coa-x" / "tools" / "coa_api_local.py"
)
NAMESPACE_ID = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("coa_api_local_under_test", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(BRIDGE_PATH.exists(), f"bridge not found at {BRIDGE_PATH}")
class BridgeNamespaceForwardingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()

    def test_import_forwards_route_namespace(self):
        captured = {}

        async def fake_call(method, target, body, **kwargs):
            captured["method"] = method
            captured["target"] = target
            captured["body"] = json.loads(body.decode("utf-8"))
            return 200, b'{"versionId":"ont-deadbeef","semver":"1.0.0"}', "application/json"

        original = self.bridge._kernel_call
        self.bridge._kernel_call = fake_call
        try:
            status, _, _ = asyncio.run(
                self.bridge._kernel_register_version(
                    "/namespaces/{namespaceId}/ontologies/{ontologyId}/import",
                    {"namespaceId": NAMESPACE_ID, "ontologyId": "fsldm-local"},
                    json.dumps({"content": "<urn:a> <urn:b> <urn:c> .", "format": "turtle"}).encode(
                        "utf-8"
                    ),
                    "tester",
                )
            )
        finally:
            self.bridge._kernel_call = original

        self.assertEqual(status, 200)
        self.assertEqual(captured["target"], "/local/ontology/register")
        self.assertEqual(captured["body"]["namespaceId"], NAMESPACE_ID)

    def test_publish_forwards_route_namespace(self):
        method, target, forwarded = self.bridge._kernel_translate(
            "/namespaces/{namespaceId}/ontologies/{ontologyId}/publish",
            {"namespaceId": NAMESPACE_ID, "ontologyId": "fsldm-local"},
            "POST",
            json.dumps({"versionId": "ont-deadbeef", "planOnly": False}).encode("utf-8"),
            {},
            "tester",
        )
        self.assertEqual(method, "POST")
        self.assertEqual(target, "/governance/publish")
        self.assertEqual(json.loads(forwarded)["namespaceId"], NAMESPACE_ID)

    def test_import_without_namespace_sends_no_field(self):
        captured = {}

        async def fake_call(method, target, body, **kwargs):
            captured["body"] = json.loads(body.decode("utf-8"))
            return 200, b'{"versionId":"ont-deadbeef"}', "application/json"

        original = self.bridge._kernel_call
        self.bridge._kernel_call = fake_call
        try:
            asyncio.run(
                self.bridge._kernel_register_version(
                    "/namespaces/{namespaceId}/ontologies/{ontologyId}/import",
                    {"ontologyId": "fsldm-local"},
                    json.dumps({"content": "<urn:a> <urn:b> <urn:c> ."}).encode("utf-8"),
                    "tester",
                )
            )
        finally:
            self.bridge._kernel_call = original

        self.assertNotIn("namespaceId", captured["body"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
