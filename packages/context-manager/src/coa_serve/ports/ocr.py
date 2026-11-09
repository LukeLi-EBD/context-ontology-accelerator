"""Document text extraction as a port (replaces Textract).

Why this port lives in ``context-manager`` rather than ``coa_ports``: it has a
single consumer — document ingestion inside this package (plan §7.2), so
pushing it into the shared package would grow an interface nobody else uses.

Shape decisions:

* **Asynchronous.** Ingestion runs inside the async request path; a sync OCR
  call would block the event loop for the length of a PDF.
* **Bytes in, structured blocks out.** The port takes the raw bytes and the
  caller's content type, not a path or an S3 key, so the same port works for
  uploads and for objects fetched from ``ObjectStorePort``.
* **Pages and blocks are explicit** because citation needs a page number and
  a bounding box; a flat text blob would make value-level provenance
  impossible to attach later.

Error contract: :class:`coa_ports.errors.PortError` only —
``INVALID_ARGUMENT`` for an unsupported content type, ``UNAVAILABLE`` for a
backend that is down, ``TIMEOUT`` past the caller's deadline, ``UNSUPPORTED``
for a document the provider cannot handle (for example a scanned image with
no OCR backend configured). No implementation may return empty text in place
of an error.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from coa_ports import NamespaceId


@dataclass(frozen=True)
class OcrBlock:
    """One layout block: a line or a paragraph, with its page and box.

    ``bbox`` is ``(left, top, right, bottom)`` in the provider's coordinate
    space, normalised to 0..1 so providers with different pixel sizes agree.
    """

    text: str
    page: int
    bbox: tuple[float, float, float, float] | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class OcrResult:
    """Extracted text for one document version.

    ``blocks`` is the primary product; ``text`` is the reading-order join of
    block text and exists for callers that only need plain text. ``provider``
    is recorded so a later citation can say where the text came from.
    """

    text: str = ""
    blocks: tuple[OcrBlock, ...] = ()
    page_count: int = 0
    provider: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)


@runtime_checkable
class OcrPort(Protocol):
    """Extract text and layout from a document's bytes."""

    async def extract(
        self,
        content: bytes,
        *,
        content_type: str,
        namespace_id: NamespaceId,
        language: str = "",
        max_pages: int = 0,
    ) -> OcrResult:
        """Extract text from ``content``.

        Args:
            content: Raw document bytes.
            content_type: MIME type, e.g. ``application/pdf``.
            namespace_id: Owning tenant; used for quota and for choosing a
                tenant-specific provider where one exists.
            language: BCP-47 hint; empty means auto-detect.
            max_pages: Stop after this many pages; ``0`` means no limit.

        Raises:
            PortError: with ``invalid_argument`` for an unsupported content
                type, ``unsupported`` when the provider cannot process this
                document, ``timeout`` past the deadline, ``unavailable`` when
                the backend is unreachable.
        """
        ...

    async def health_check(self) -> Mapping[str, Any]:
        """Probe reachability; never raises (COA contract requirement)."""
        ...


__all__ = ["OcrBlock", "OcrPort", "OcrResult"]
