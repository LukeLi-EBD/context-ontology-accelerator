"""Shape guard for the OCR port owned by ``context-manager``.

No implementation is wired yet. These tests pin the async contract and the
requirement that blocks carry a page number, because citation depends on it.
"""

from __future__ import annotations

import inspect

import pytest

from coa_serve.ports import OcrBlock, OcrPort, OcrResult


def test_port_is_a_runtime_checkable_protocol() -> None:
    assert getattr(OcrPort, "_is_runtime_protocol", False)


def test_extract_and_health_check_are_async() -> None:
    assert inspect.iscoroutinefunction(OcrPort.extract)
    assert inspect.iscoroutinefunction(OcrPort.health_check)


def test_extract_takes_bytes_not_a_path_or_object_key() -> None:
    parameters = inspect.signature(OcrPort.extract).parameters
    assert "content" in parameters
    assert "content_type" in parameters
    assert "namespace_id" in parameters


def test_structural_match_accepts_a_minimal_provider() -> None:
    class Stub:
        async def extract(self, content, *, content_type, namespace_id, language="", max_pages=0):
            return OcrResult(text="hello", page_count=1)

        async def health_check(self):
            return {"status": "ok"}

    assert isinstance(Stub(), OcrPort)


def test_blocks_carry_page_numbers_for_citation() -> None:
    block = OcrBlock(text="revenue", page=3)
    assert block.page == 3
    assert block.bbox is None


@pytest.mark.parametrize("field", ["text", "blocks", "page_count", "provider"])
def test_result_exposes_the_fields_downstream_consumers_need(field: str) -> None:
    assert field in OcrResult.__dataclass_fields__
