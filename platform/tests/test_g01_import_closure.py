"""G-01 second-half unit tests: owl:imports closure (no SHACL/publish).

Run without rebuilding the image:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g01_import_closure.py
"""

import tempfile
import unittest
from pathlib import Path

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

LOCAL_IMPORT = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

<https://w3id.org/fsldm/agreement> a owl:Ontology ;
    owl:imports <https://w3id.org/fsldm/party> .
ex:Agreement a owl:Class .
"""

PARTY_TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

ex:Party a owl:Class .
ex:member a owl:ObjectProperty .
"""

MISSING_IMPORT = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

ex:ClassA a owl:Class ;
    owl:imports <https://w3id.org/fsldm/does-not-exist> .
"""

NESTED_ROOT = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

ex:ClassA a owl:Class ;
    owl:imports <https://w3id.org/fsldm/level-b> .
"""

LEVEL_B = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

ex:LevelB a owl:Class ;
    owl:imports <https://w3id.org/fsldm/level-c> .
"""

LEVEL_C = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/tbox#> .

ex:LevelC a owl:Class .
"""


def write(tmp: Path, name: str, text: str) -> None:
    (tmp / name).write_text(text, encoding="utf-8")


class ClosureTests(unittest.TestCase):
    def test_no_imports_reason_is_shacl_not_deployed(self):
        result = parse_import_document(VALID_TTL.encode("utf-8"), search_dirs=["/nonexistent"])
        self.assertEqual(result["importsResolved"], [])
        self.assertEqual(result["unresolvedImports"], [])
        self.assertEqual(result["totalTriples"], result["triples"])
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_SHACL_NOT_DEPLOYED")

    def test_local_import_resolves_and_increases_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), "party.ttl", PARTY_TTL)
            result = parse_import_document(
                LOCAL_IMPORT.encode("utf-8"), search_dirs=[tmp]
            )
        self.assertEqual(len(result["importsResolved"]), 1)
        self.assertEqual(result["importsResolved"][0]["source"], "local-file")
        self.assertEqual(result["unresolvedImports"], [])
        self.assertGreater(result["totalTriples"], result["triples"])
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_SHACL_NOT_DEPLOYED")

    def test_missing_import_is_critical_and_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = parse_import_document(
                MISSING_IMPORT.encode("utf-8"), search_dirs=[tmp]
            )
        self.assertEqual(len(result["unresolvedImports"]), 1)
        item = result["unresolvedImports"][0]
        self.assertFalse(item["resolved"])
        self.assertTrue(item["critical"])
        self.assertEqual(item["reason"], "E_IMPORTS_OFFLINE")
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_IMPORTS_UNRESOLVED")

    def test_two_level_nesting_resolves_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), "level-b.ttl", LEVEL_B)
            write(Path(tmp), "level-c.ttl", LEVEL_C)
            result = parse_import_document(NESTED_ROOT.encode("utf-8"), search_dirs=[tmp])
        self.assertEqual(len(result["importsResolved"]), 2)
        self.assertEqual(
            {item["iri"] for item in result["importsResolved"]},
            {"https://w3id.org/fsldm/level-b", "https://w3id.org/fsldm/level-c"},
        )
        self.assertFalse(result["usable"])
        self.assertEqual(result["reason"], "E_SHACL_NOT_DEPLOYED")

    def test_cycle_raises_explicit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), "level-b.ttl", LEVEL_B)
            write(Path(tmp), "level-c.ttl", LEVEL_C.replace(
                "ex:LevelC a owl:Class .",
                "ex:LevelC a owl:Class ;\n    owl:imports <https://w3id.org/fsldm/level-b> ."))
            with self.assertRaises(PortError) as ctx:
                parse_import_document(NESTED_ROOT.encode("utf-8"), search_dirs=[tmp])
        self.assertEqual(ctx.exception.provider_code, "E_IMPORTS_CYCLE")

    def test_syntax_error_still_reports_line_and_column(self):
        with self.assertRaises(PortError) as ctx:
            parse_import_document(BAD_TTL.encode("utf-8"), search_dirs=["/nonexistent"])
        self.assertEqual(ctx.exception.provider_code, "E_ONTOLOGY_PARSE")
        self.assertEqual(ctx.exception.details["line"], 4)
        self.assertGreater(ctx.exception.details["column"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
