"""G-01 first-half unit tests: parse + honest counts (no closure/SHACL/publish).

Run without rebuilding the image:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g01_import_parse.py
"""

import unittest

from platform_core.adapters.ontology_pg import parse_import_document
from platform_core.errors import PortError

VALID_TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

ex:ClassA a owl:Class .
ex:ClassB a owl:Class .
ex:relates a owl:ObjectProperty .
ex:label a owl:DatatypeProperty .
"""

BAD_TTL = """\
@prefix ex: <http://e/> .
ex:a ex:b ex:c .
ex:d ex:e ex:f ;
  bad
"""

IMPORTS_TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

<https://w3id.org/fsldm/core> a owl:Ontology ;
    owl:imports <https://w3id.org/fsldm/party> .
ex:ClassA a owl:Class .
"""


class ParseImportTests(unittest.TestCase):
    def test_valid_ttl_counts_and_reason(self):
        result = parse_import_document(
            VALID_TTL.encode("utf-8"),
            target_namespace="http://example.org/tbox#",
            author="tester",
            change_summary="initial",
        )
        self.assertEqual(result["triples"], 4)
        self.assertEqual(result["classes"], 2)
        self.assertEqual(result["objectProperties"], 1)
        self.assertEqual(result["dataProperties"], 1)
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_SHACL_NOT_DEPLOYED")
        self.assertEqual(result["unresolvedImports"], [])
        self.assertTrue(result["importId"].startswith("imp-"))
        self.assertEqual(result["author"], "tester")
        self.assertEqual(result["changeSummary"], "initial")

    def test_syntax_error_reports_real_line_and_column(self):
        with self.assertRaises(PortError) as ctx:
            parse_import_document(BAD_TTL.encode("utf-8"))
        error = ctx.exception
        self.assertEqual(error.provider_code, "E_ONTOLOGY_PARSE")
        self.assertEqual(error.details["line"], 4)
        self.assertIsInstance(error.details["column"], int)
        self.assertGreater(error.details["column"], 0)
        self.assertEqual(error.details["columnSource"], "rdflib:_i")

    def test_owl_imports_is_not_silently_empty(self):
        result = parse_import_document(IMPORTS_TTL.encode("utf-8"))
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_IMPORTS_UNRESOLVED")
        self.assertEqual(len(result["unresolvedImports"]), 1)
        self.assertEqual(
            result["unresolvedImports"][0]["iri"], "https://w3id.org/fsldm/party"
        )
        self.assertEqual(
            result["unresolvedImports"][0]["reason"],
            "E_IMPORTS_OFFLINE",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
