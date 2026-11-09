"""G-01 SHACL integration tests (deployed-shapes lookup + violations).

Run without rebuilding the image:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g01_import_shacl.py
"""

import tempfile
import unittest
from pathlib import Path

from platform_core.adapters.ontology_pg import parse_import_document

NAMESPACE = "https://w3id.org/fsldm/"

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix fsldm: <https://w3id.org/fsldm/> .

fsldm:ClassLabelShape a sh:NodeShape ;
    sh:targetClass owl:Class ;
    sh:property [
        sh:path rdfs:label ;
        sh:minCount 1 ;
        sh:message "owl:Class must carry rdfs:label" ;
    ] .
"""

BAD_CLASS = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<https://w3id.org/fsldm/Agreement> a owl:Class .
"""

GOOD_CLASS = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://w3id.org/fsldm/Agreement> a owl:Class ;
    rdfs:label "Agreement"@en .
"""

MISSING_IMPORT_AND_LABEL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

<https://w3id.org/fsldm/Agreement> a owl:Class ;
    owl:imports <https://w3id.org/fsldm/does-not-exist> .
"""


def deploy_shapes(root: Path) -> str:
    directory = root / "fsldm"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "shapes.ttl").write_text(SHAPES_TTL, encoding="utf-8")
    (directory / "manifest.json").write_text(
        '{"id": "fsldm-shapes", "version": "0.1.0", '
        '"namespace": "https://w3id.org/fsldm/"}',
        encoding="utf-8",
    )
    return str(root)


class ShaclIntegrationTests(unittest.TestCase):
    def test_missing_label_yields_focus_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            shapes_dir = deploy_shapes(Path(tmp))
            result = parse_import_document(
                BAD_CLASS.encode("utf-8"),
                target_namespace=NAMESPACE,
                shapes_dir=shapes_dir,
            )
        self.assertEqual(result["shacl"]["status"], "validated")
        self.assertFalse(result["shacl"]["conforms"])
        self.assertGreater(len(result["shacl"]["violations"]), 0)
        for item in result["shacl"]["violations"]:
            self.assertIsNotNone(item["focusNode"])
        self.assertEqual(
            result["shacl"]["violations"][0]["focusNode"],
            "https://w3id.org/fsldm/Agreement",
        )
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_SHACL_VIOLATION")
        self.assertEqual(result["shacl"]["shapesId"], "fsldm-shapes")
        self.assertEqual(result["shacl"]["shapesVersion"], "0.1.0")

    def test_compliant_class_conforms_and_consistency_decides_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            shapes_dir = deploy_shapes(Path(tmp))
            result = parse_import_document(
                GOOD_CLASS.encode("utf-8"),
                target_namespace=NAMESPACE,
                shapes_dir=shapes_dir,
                consistency_checker=lambda _nt: {"consistent": True, "engine": "stub"},
            )
        self.assertTrue(result["shacl"]["conforms"])
        self.assertEqual(result["shacl"]["violations"], [])
        self.assertEqual(result["consistency"]["status"], "consistent")
        self.assertTrue(result["usable"])
        self.assertIsNone(result["reason"])
        # usable does not mean published: staging only.
        self.assertFalse(result["published"])
        self.assertNotEqual(
            result["shacl"]["engine"].get("version"), None, result["shacl"]["engine"]
        )

    def test_no_deployed_shapes_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = parse_import_document(
                GOOD_CLASS.encode("utf-8"),
                target_namespace=NAMESPACE,
                shapes_dir=tmp,
            )
        self.assertEqual(result["shacl"]["status"], "not_deployed")
        self.assertIsNone(result["shacl"]["conforms"])
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_SHACL_NOT_DEPLOYED")

    def test_closure_failure_outranks_shacl_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            shapes_dir = deploy_shapes(Path(tmp))
            result = parse_import_document(
                MISSING_IMPORT_AND_LABEL.encode("utf-8"),
                target_namespace=NAMESPACE,
                shapes_dir=shapes_dir,
                search_dirs=[tmp],
            )
        self.assertFalse(result["usable"])
        self.assertEqual(result["shacl"]["conforms"], False)
        self.assertTrue(result["unresolvedImports"])
        self.assertEqual(result["reason"], "E_IMPORTS_UNRESOLVED")
        codes = {item["code"] for item in result["usableReasons"]}
        self.assertIn("E_SHACL_VIOLATION", codes)
        self.assertIn("E_IMPORTS_UNRESOLVED", codes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
