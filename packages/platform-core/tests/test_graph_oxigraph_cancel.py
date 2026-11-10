"""Oxigraph reports ``serve --timeout-s`` cancellation as HTTP 200 with the payload
cut short and a notice appended. Every call has to treat that as a failure: the
status code alone would let a caller page through a partial answer, or report a
half-applied write as done.
"""

from __future__ import annotations

import httpx
import pytest

from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.errors import PortError

pytestmark = pytest.mark.unit

CANCELLED_NOTICE = "The SPARQL operation has been cancelled"
_ROW = '{"head":{"vars":["a"]},"results":{"bindings":[{"a":{"type":"uri","value":"urn:x"}}]}}'


def _store(handler) -> OxigraphHttpStore:
    store = OxigraphHttpStore("http://oxigraph.test")
    store._client.close()
    store._client = httpx.Client(base_url="http://oxigraph.test", transport=httpx.MockTransport(handler))
    return store


class TestCancelledResponse:
    def test_a_truncated_json_body_is_a_deadline_exceeded(self):
        store = _store(lambda request: httpx.Response(200, text=_ROW[:-3] + CANCELLED_NOTICE))
        with pytest.raises(PortError) as exc:
            store.query("SELECT * WHERE { ?s ?p ?o }")
        assert exc.value.code == "DeadlineExceeded"
        assert exc.value.provider_code == "E_GRAPH_TIMEOUT"

    def test_a_body_that_is_complete_json_plus_the_notice_is_still_a_deadline(self):
        # The cut can land exactly after the last complete row: the JSON alone
        # would parse, and the caller would page through a partial answer.
        store = _store(lambda request: httpx.Response(200, text=_ROW + CANCELLED_NOTICE))
        with pytest.raises(PortError) as exc:
            store.query("SELECT * WHERE { ?s ?p ?o }")
        assert exc.value.code == "DeadlineExceeded"

    def test_a_cancelled_ask_is_not_false(self):
        store = _store(lambda request: httpx.Response(200, text='{"boolean":true}' + CANCELLED_NOTICE))
        with pytest.raises(PortError) as exc:
            store.ask("ASK { ?s ?p ?o }")
        assert exc.value.code == "DeadlineExceeded"

    def test_a_cancelled_update_is_not_a_success(self):
        store = _store(lambda request: httpx.Response(200, text=CANCELLED_NOTICE))
        with pytest.raises(PortError) as exc:
            store.update("INSERT DATA { <urn:s> <urn:p> <urn:o> }")
        assert exc.value.code == "DeadlineExceeded"

    def test_a_cancelled_export_is_not_partial_turtle(self):
        store = _store(lambda request: httpx.Response(200, text="<urn:s> <urn:p> <urn:o> .\n" + CANCELLED_NOTICE))
        with pytest.raises(PortError) as exc:
            store.export_graph("urn:platform:test")
        assert exc.value.code == "DeadlineExceeded"

    def test_the_sentence_inside_a_result_does_not_trigger(self):
        body = (
            '{"head":{"vars":["a"]},"results":{"bindings":[{"a":{"type":"literal","value":"'
            + CANCELLED_NOTICE
            + '"}}]}}'
        )
        store = _store(lambda request: httpx.Response(200, text=body))
        rows = store.query("SELECT * WHERE { ?s ?p ?o }")
        assert rows["bindings"][0]["values"]["a"]["value"] == CANCELLED_NOTICE

    def test_a_normal_result_is_returned(self):
        store = _store(lambda request: httpx.Response(200, text=_ROW))
        assert store.query("SELECT * WHERE { ?s ?p ?o }")["bindings"]
