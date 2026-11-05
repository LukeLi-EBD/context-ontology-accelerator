"""G-01 consistency gate tests (real reasoner container + fault injection).

Reasoner is already running; tests never start containers:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g01_import_consistency.py
"""

import sys
import tempfile
import time
import unittest
from pathlib import Path

from platform_core.adapters.reasoner_robot import ReasonerClient
from platform_core.adapters.ontology_pg import parse_import_document
from platform_core.config import ReasoningConfig
from platform_core.errors import PortError

sys.path.insert(0, str(Path(__file__).parent))
from test_g01_import_shacl import deploy_shapes, NAMESPACE  # noqa: E402

CONSISTENT_TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://w3id.org/fsldm/Agreement> a owl:Class ;
    rdfs:label "Agreement"@en .
"""

DISJOINT_TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <https://w3id.org/fsldm/> .

ex:Alpha a owl:Class ; rdfs:label "Alpha"@en .
ex:Beta a owl:Class ; rdfs:label "Beta"@en .
ex:Alpha owl:disjointWith ex:Beta .
ex:both a owl:NamedIndividual, ex:Alpha, ex:Beta .
"""


def real_checker(endpoint: str = "http://host.docker.internal:7879", timeout_ms: int = 120000):
    config = ReasoningConfig(endpoint=endpoint, timeout_ms=timeout_ms, profile="EL")
    client = ReasonerClient(config)

    def check(tbox_nt: bytes):
        return client.reason(tbox_nt, b"", profile="EL", consistency_first=True)

    return check, client


class ConsistencyTests(unittest.TestCase):
    def test_consistent_import_is_usable_but_not_published(self):
        check, client = real_checker()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                shapes_dir = deploy_shapes(Path(tmp))
                result = parse_import_document(
                    CONSISTENT_TTL.encode(),
                    target_namespace=NAMESPACE,
                    shapes_dir=shapes_dir,
                    consistency_checker=check,
                )
        finally:
            client.close()
        self.assertEqual(result["consistency"]["status"], "consistent")
        self.assertTrue(result["consistency"]["consistent"])
        self.assertTrue(result["usable"])
        self.assertIsNone(result["reason"])
        self.assertFalse(result["published"])

    def test_disjoint_classes_conflict_is_not_usable(self):
        check, client = real_checker()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                shapes_dir = deploy_shapes(Path(tmp))
                result = parse_import_document(
                    DISJOINT_TTL.encode(),
                    target_namespace=NAMESPACE,
                    shapes_dir=shapes_dir,
                    consistency_checker=check,
                )
        finally:
            client.close()
        self.assertEqual(result["consistency"]["status"], "inconsistent")
        self.assertFalse(result["consistency"]["consistent"])
        self.assertIn(
            result["consistency"]["detail"],
            {"Alpha", "Beta", "both", "engine-reason-unknown"},
            result["consistency"],
        )
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_CONSISTENCY_FAILED")

    def test_reasoner_unreachable_reports_unavailable(self):
        check, client = real_checker(endpoint="http://host.docker.internal:9", timeout_ms=1000)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                shapes_dir = deploy_shapes(Path(tmp))
                result = parse_import_document(
                    CONSISTENT_TTL.encode(),
                    target_namespace=NAMESPACE,
                    shapes_dir=shapes_dir,
                    consistency_checker=check,
                )
        finally:
            client.close()
        self.assertEqual(result["consistency"]["status"], "unavailable")
        self.assertIsNone(result["consistency"]["consistent"])
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_CONSISTENCY_UNAVAILABLE")

    def test_timeout_aborts_instead_of_hanging(self):
        def slow(_nt):
            time.sleep(2)
            return {"consistent": True}

        with tempfile.TemporaryDirectory() as tmp:
            shapes_dir = deploy_shapes(Path(tmp))
            started = time.monotonic()
            result = parse_import_document(
                CONSISTENT_TTL.encode(),
                target_namespace=NAMESPACE,
                shapes_dir=shapes_dir,
                consistency_checker=slow,
                consistency_timeout_s=0.2,
            )
            elapsed = time.monotonic() - started
        self.assertEqual(result["consistency"]["status"], "timeout")
        self.assertIsNone(result["consistency"]["consistent"])
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_CONSISTENCY_TIMEOUT")
        self.assertLess(elapsed, 1.5, f"timeout did not bail out: {elapsed:.2f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
