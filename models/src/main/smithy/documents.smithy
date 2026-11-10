// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Document ingestion + fact-candidate approval operations.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.1 rows for UploadDocument,
// ListDocuments, ListDocumentChunks, ListFactCandidates, ApproveFactCandidate
// and RejectFactCandidate. Paths are namespace-scoped like every other
// operation; the service definition lives in control-plane.smithy.
$version: "2"

namespace com.amazon.semanticcontext.documents

use com.amazon.semanticcontext.common#ConflictError
use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#PaginatedOutput
use com.amazon.semanticcontext.common#PaginationToken
use com.amazon.semanticcontext.common#Uuid

/// Human-readable document title. Defaults to the uploaded filename.
@length(min: 1, max: 512)
string DocumentTitle

/// Key of a caller-metadata entry.
@length(min: 1, max: 128)
string MetadataKey

/// Value of a caller-metadata entry.
@length(min: 0, max: 2048)
string MetadataValue

/// Free-form document metadata carried through ingestion.
map DocumentMetadata {
    key: MetadataKey
    value: MetadataValue
}

/// Lifecycle status of an ingested document.
enum DocumentStatus {
    /// Bytes stored, ingestion not started.
    UPLOADED

    /// Ingestion (chunking/embedding/extraction) in progress.
    PROCESSING

    /// Chunks, embeddings and fact candidates exist.
    INDEXED

    /// Ingestion failed; the document row keeps the error reason.
    FAILED
}

/// One document in the namespace's ingestion registry.
structure DocumentSummary {
    /// Identifier assigned by UploadDocument.
    @required
    documentId: Uuid

    /// Display title (caller-supplied, else the filename).
    @required
    title: String

    /// Current lifecycle status.
    @required
    status: DocumentStatus

    /// Number of chunks written for this document.
    @required
    chunkCount: Integer

    /// Timestamp of the last status change (RFC 3339).
    ///
    /// Declared as a string, like the other summary types in this service, so
    /// the wire value is the stored RFC 3339 text rather than an epoch number.
    @required
    updatedAt: String

    /// Why ingestion failed. Present only when `status` is `FAILED`.
    errorMessage: String
}

list DocumentSummaryList {
    member: DocumentSummary
}

/// One text chunk of a document.
structure DocumentChunk {
    /// Identifier of the chunk; also the entity URI suffix used by its embedding.
    @required
    chunkId: Uuid

    /// 1-based page number the chunk came from (1 for plain-text sources).
    @required
    page: Integer

    /// Chunk text exactly as indexed.
    @required
    text: String

    /// Inclusive character offset of the chunk in the normalised document text.
    @required
    charStart: Integer

    /// Exclusive character offset of the chunk in the normalised document text.
    @required
    charEnd: Integer
}

list DocumentChunkList {
    member: DocumentChunk
}

/// Review status of an extracted fact candidate.
enum FactCandidateStatus {
    /// Awaiting steward review.
    PENDING

    /// Approved; a fact row and an A-Box triple exist.
    APPROVED

    /// Rejected; kept for audit, never projected into the A-Box.
    REJECTED
}

/// One subject-predicate-object candidate extracted from a document chunk.
structure FactCandidate {
    /// Identifier assigned at extraction time.
    @required
    candidateId: Uuid

    /// Subject IRI or literal label as extracted.
    @required
    subject: String

    /// Predicate IRI or label as extracted.
    @required
    predicate: String

    /// Object IRI or literal label as extracted.
    @required
    object: String

    /// Extractor confidence in [0, 1].
    @required
    confidence: Float

    /// Review status.
    @required
    status: FactCandidateStatus

    /// Document the candidate was extracted from.
    documentId: Uuid

    /// Chunk the candidate was extracted from.
    chunkId: Uuid

    /// Source sentence the candidate was extracted from.
    evidence: String
}

list FactCandidateList {
    member: FactCandidate
}

/// Field name of a fact override (`subject`, `predicate` or `object`).
@length(min: 1, max: 32)
string FactOverrideKey

/// Replacement value for one fact field.
@length(min: 1, max: 2048)
string FactOverrideValue

/// Overrides applied to the fact written when a candidate is approved. Keys are
/// `subject`, `predicate` and `object`; absent keys keep the candidate values.
map FactOverrides {
    key: FactOverrideKey
    value: FactOverrideValue
}

// ── Documents ───────────────────────────────────────────────────────────────
/// Store a document's bytes and register it for ingestion.
///
/// `contentBase64` carries the bytes. The content hash is computed server-side
/// from the decoded bytes, so the returned `contentHash` is always the hash of
/// what was stored; `contentSha256`, when supplied, is verified against it.
/// Re-uploading identical bytes into the same namespace answers 409 with the
/// existing document id.
@http(method: "POST", uri: "/namespaces/{namespaceId}/documents", code: 201)
@examples([
    {
        title: "Upload a plain-text policy"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", filename: "loan-policy.txt", contentType: "text/plain", contentBase64: "5L+d6K+B6LS35qy+5pS/562W" }
        output: { documentId: "9a7b6c5d-4e3f-4a2b-8c1d-0e9f8a7b6c5d", version: 1, contentHash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", status: "PROCESSING" }
    }
])
operation UploadDocument {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Original filename, including extension.
        @required
        @length(min: 1, max: 512)
        filename: String

        /// MIME type of the uploaded bytes, e.g. `text/plain`.
        @required
        @length(min: 1, max: 255)
        contentType: String

        /// Base64-encoded document content.
        @length(min: 1, max: 10485760)
        contentBase64: String

        /// SHA-256 of the content (lowercase hex). Optional when
        /// `contentBase64` is supplied — if present it must match the decoded
        /// bytes, and is rejected rather than ignored when it does not.
        @length(min: 64, max: 64)
        contentSha256: String

        /// Display title; defaults to `filename`.
        title: DocumentTitle

        /// Caller metadata stored on the document row.
        @length(min: 0, max: 20)
        metadata: DocumentMetadata
    }

    output := {
        /// Identifier of the stored document.
        @required
        documentId: Uuid

        /// Document version (1 for the first upload of these bytes).
        @required
        version: Integer

        /// SHA-256 of the stored bytes, lowercase hex.
        @required
        contentHash: String

        /// Lifecycle status at response time (`UPLOADED` or `PROCESSING`).
        @required
        status: DocumentStatus
    }

    errors: [
        ConflictError
    ]
}

/// List documents registered in the namespace, newest first.
@http(method: "GET", uri: "/namespaces/{namespaceId}/documents")
@readonly
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "maxResults", items: "items")
@examples([
    {
        title: "List the namespace's documents"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11" }
        output: {
            items: []
        }
    }
])
operation ListDocuments {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Optional lifecycle-status filter.
        @httpQuery("status")
        status: DocumentStatus

        /// Pagination token from a previous response.
        @httpQuery("nextToken")
        nextToken: PaginationToken

        /// Maximum documents per page (default and maximum 100).
        @httpQuery("maxResults")
        @range(min: 1, max: 100)
        maxResults: Integer
    }

    output := with [PaginatedOutput] {
        /// Page of document summaries.
        @required
        items: DocumentSummaryList
    }
}

/// List the chunks of one document in document order.
@http(method: "GET", uri: "/namespaces/{namespaceId}/documents/{documentId}/chunks")
@readonly
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "maxResults", items: "items")
@examples([
    {
        title: "List one document's chunks"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", documentId: "9a7b6c5d-4e3f-4a2b-8c1d-0e9f8a7b6c5d" }
        output: {
            items: [
                {
                    chunkId: "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d"
                    page: 1
                    text: "示例切片文本"
                    charStart: 0
                    charEnd: 6
                }
            ]
        }
    }
])
operation ListDocumentChunks {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Document whose chunks to list.
        @required
        @httpLabel
        documentId: Uuid

        /// Pagination token from a previous response.
        @httpQuery("nextToken")
        nextToken: PaginationToken

        /// Maximum chunks per page (default and maximum 200).
        @httpQuery("maxResults")
        @range(min: 1, max: 200)
        maxResults: Integer
    }

    output := with [PaginatedOutput] {
        /// Page of chunks, ordered by `charStart`.
        @required
        items: DocumentChunkList
    }

    errors: [
        NotFoundError
    ]
}

// ── Fact candidates ─────────────────────────────────────────────────────────
/// List extracted fact candidates awaiting review (or filtered by status).
@http(method: "GET", uri: "/namespaces/{namespaceId}/candidates")
@readonly
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "maxResults", items: "items")
@examples([
    {
        title: "List pending candidates"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", status: "PENDING" }
        output: {
            items: []
        }
    }
])
operation ListFactCandidates {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Only candidates extracted from this document.
        @httpQuery("documentId")
        documentId: Uuid

        /// Only candidates in this review status (default: all).
        @httpQuery("status")
        status: FactCandidateStatus

        /// Pagination token from a previous response.
        @httpQuery("nextToken")
        nextToken: PaginationToken

        /// Maximum candidates per page (default and maximum 200).
        @httpQuery("maxResults")
        @range(min: 1, max: 200)
        maxResults: Integer
    }

    output := with [PaginatedOutput] {
        /// Page of candidates, newest first.
        @required
        items: FactCandidateList
    }
}

/// Approve a candidate: write the fact to the ledger and project it into the
/// namespace A-Box graph. Idempotent per candidate; a second approval answers
/// 409 with the fact id already written.
@http(method: "POST", uri: "/namespaces/{namespaceId}/candidates/{candidateId}/approve", code: 200)
@examples([
    {
        title: "Approve a candidate"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", candidateId: "3c4d5e6f-7081-492a-8b3c-4d5e6f708192" }
        output: { factId: "4d5e6f70-8192-4a3b-9c4d-5e6f708192a3", status: "APPROVED" }
    }
])
operation ApproveFactCandidate {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        @required
        @httpLabel
        candidateId: Uuid

        /// Identity of the approving principal; defaults to the caller.
        @length(min: 1, max: 256)
        actor: String

        /// Values overriding the extracted subject/predicate/object.
        @length(min: 0, max: 3)
        factOverrides: FactOverrides
    }

    output := {
        /// Identifier of the written fact.
        @required
        factId: Uuid

        /// Candidate status after the call (`APPROVED`).
        @required
        status: FactCandidateStatus
    }

    errors: [
        ConflictError
        NotFoundError
    ]
}

/// Reject a candidate. The row is kept for audit; nothing is written to the
/// fact ledger or the A-Box graph.
@http(method: "POST", uri: "/namespaces/{namespaceId}/candidates/{candidateId}/reject", code: 200)
@examples([
    {
        title: "Reject a candidate"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", candidateId: "3c4d5e6f-7081-492a-8b3c-4d5e6f708192", reason: "Predicate is too generic to publish." }
        output: { status: "REJECTED" }
    }
])
operation RejectFactCandidate {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        @required
        @httpLabel
        candidateId: Uuid

        /// Identity of the rejecting principal; defaults to the caller.
        @length(min: 1, max: 256)
        actor: String

        /// Why the candidate was rejected.
        @required
        @length(min: 1, max: 1024)
        reason: String
    }

    output := {
        /// Candidate status after the call (`REJECTED`).
        @required
        status: FactCandidateStatus
    }

    errors: [
        NotFoundError
    ]
}
