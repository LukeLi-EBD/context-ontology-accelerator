"""Provider selection: defaults, explicit disable, and loud failures."""

from __future__ import annotations

import unittest

from coa_gateway import (
    DEFAULTS,
    FusekiGraphClient,
    InMemoryVectorClient,
    OxigraphGraphClient,
    ProviderNotConfigured,
    ProviderSettings,
    UnknownProviderError,
    build_client,
    build_gateway,
)


class ProviderSettingsTest(unittest.TestCase):
    def test_defaults_match_sample(self) -> None:
        settings = ProviderSettings.from_mapping({})
        self.assertEqual(
            {name: settings.provider(name) for name in DEFAULTS},
            {
                "graph": "oxigraph",
                "vector": "in-memory",
                "embedding": "none",
                "llm": "none",
                "query_executor": "none",
                "source_catalog": "none",
                "conversation": "none",
                "memory": "none",
                "object_store": "none",
            },
        )

    def test_graph_provider_selects_implementation(self) -> None:
        oxigraph = build_client("graph", ProviderSettings.from_mapping({}))
        self.assertIsInstance(oxigraph, OxigraphGraphClient)
        self.assertEqual(oxigraph._query_url, "http://oxigraph:7878/query")

        fuseki = build_client(
            "graph",
            ProviderSettings.from_mapping(
                {"COA_PROVIDER_GRAPH": "fuseki", "COA_GRAPH_FUSEKI_URL": "http://fuseki:3030/ds/sparql"}
            ),
        )
        self.assertIsInstance(fuseki, FusekiGraphClient)
        self.assertEqual(fuseki._query_url, "http://fuseki:3030/ds/sparql")

    def test_unknown_provider_raises(self) -> None:
        with self.assertRaises(UnknownProviderError) as caught:
            build_client("graph", ProviderSettings.from_mapping({"COA_PROVIDER_GRAPH": "oxigraph-http"}))
        self.assertIn("oxigraph-http", str(caught.exception))
        self.assertIn("supported", str(caught.exception))

    def test_fuseki_requires_endpoint_and_does_not_fall_back(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("graph", ProviderSettings.from_mapping({"COA_PROVIDER_GRAPH": "fuseki"}))
        self.assertIn("COA_GRAPH_FUSEKI_URL", str(caught.exception))
        self.assertIn("refusing to fall back", str(caught.exception))

    def test_neptune_requires_aws_shaped_config(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("graph", ProviderSettings.from_mapping({"COA_PROVIDER_GRAPH": "neptune"}))
        self.assertIn("COA_GRAPH_NEPTUNE_ENDPOINT", str(caught.exception))

        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client(
                "graph",
                ProviderSettings.from_mapping(
                    {
                        "COA_PROVIDER_GRAPH": "neptune",
                        "COA_GRAPH_NEPTUNE_ENDPOINT": "https://neptune.example:8182",
                    }
                ),
            )
        self.assertIn("AWS_REGION", str(caught.exception))
        self.assertIn("refusing to fall back", str(caught.exception))

    def test_memory_sqlite_requires_path(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("memory", ProviderSettings.from_mapping({"COA_PROVIDER_MEMORY": "sqlite"}))
        self.assertIn("COA_MEMORY_SQLITE_PATH", str(caught.exception))
        self.assertIn("refusing to fall back", str(caught.exception))

    def test_llama_cpp_requires_model_path(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("llm", ProviderSettings.from_mapping({"COA_PROVIDER_LLM": "llama-cpp"}))
        self.assertIn("COA_LLM_LLAMA_CPP_MODEL_PATH", str(caught.exception))
        self.assertIn("refusing to fall back", str(caught.exception))

    def test_none_disables_interface_without_substitution(self) -> None:
        gateway = build_gateway(
            ProviderSettings.from_mapping({"COA_PROVIDER_GRAPH": "none", "COA_PROVIDER_VECTOR": "none"})
        )
        self.assertFalse(gateway.capabilities()["graph"])
        self.assertFalse(gateway.capabilities()["vector"])
        with self.assertRaises(ProviderNotConfigured):
            _ = gateway.graph_client

    def test_vector_provider_selects_in_memory(self) -> None:
        client = build_client(
            "vector", ProviderSettings.from_mapping({"COA_VECTOR_IN_MEMORY_PATH": "D:/tmp/vectors.jsonl"})
        )
        self.assertIsInstance(client, InMemoryVectorClient)

    def test_vector_aoss_is_declared_but_unwired(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("vector", ProviderSettings.from_mapping({"COA_PROVIDER_VECTOR": "aoss"}))
        self.assertIn("not wired", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
