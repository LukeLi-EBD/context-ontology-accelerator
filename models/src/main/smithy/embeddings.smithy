// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Entity-embedding read operations.
//
// Spec: doc/coa-x/11-复盘与规划.md (M1a 收口后的契约补齐). The ontology engine
// already serves these two reads, but they were only reachable through the
// local bridge — no operation existed in the contract, so the web app called
// them with the untyped `ApiClient`. Declaring them here puts the capability
// behind the same generated client as every other route.
//
// Wire shape: the upstream engine answers with a bare JSON array. The gateway
// normalises that to `{"embeddings": [...]}` so restJson1 (which requires an
// operation output to be a structure) can describe the response with a typed
// list instead of a free-form document.
$version: "2"

namespace com.amazon.semanticcontext.embeddings

use com.amazon.semanticcontext.common#Uuid

/// Entity type an embedding row was written for (e.g. `class`, `property`,
/// `chunk`).
@length(min: 1, max: 64)
string EmbeddingEntityType

/// Kind of vector held by one embedding row (e.g. `lexical`, `structural`,
/// `chunk`).
@length(min: 1, max: 64)
string EmbeddingType

/// Identifier of the model that produced the vectors (e.g. a local BGE model
/// id).
@length(min: 1, max: 256)
string EmbeddingModelId

/// Dense float vector.
@length(min: 1, max: 8192)
list DoubleList {
    /// One component. Bounded well outside the range any supported embedding
    /// model produces; the bound exists to keep an absurd payload from being
    /// forwarded to the vector store.
    @range(min: -1000, max: 1000)
    member: Double
}

/// Free-form metadata attached to an embedding row (document/chunk provenance
/// for chunk vectors). Values keep their JSON type, so this is a document
/// rather than a string map.
document EmbeddingMetadata

/// One stored embedding, vector included.
///
/// Member names mirror the engine's snake_case JSON through `@jsonName`; the
/// camelCase names here are the contract's own spelling.
structure EmbeddingRecord {
    /// Row identity. Empty for k-NN hits, which carry no stable external id.
    @required
    id: String

    /// Ontology (or A-Box/namespace) the vector belongs to.
    @required
    @jsonName("ontology_id")
    ontologyId: String

    /// URI of the embedded entity.
    @required
    @jsonName("entity_uri")
    entityUri: String

    /// Entity type the row was written for.
    @required
    @jsonName("entity_type")
    entityType: EmbeddingEntityType

    /// Kind of vector in this row.
    @required
    @jsonName("embedding_type")
    embeddingType: EmbeddingType

    /// Model that produced the vector.
    @required
    @jsonName("model_id")
    modelId: EmbeddingModelId

    /// Vector length.
    @required
    dimensions: Integer

    /// Source text, when the row was written from text (chunk rows carry it).
    text: String

    /// Row creation timestamp (RFC 3339); empty for k-NN hits.
    @jsonName("created_at")
    createdAt: String

    /// Provenance metadata, e.g. chunk/document ids for chunk vectors.
    metadata: EmbeddingMetadata

    /// The raw vector.
    @required
    vector: DoubleList
}

list EmbeddingRecordList {
    member: EmbeddingRecord
}

/// Envelope for the embedding reads. The engine returns a bare array; the
/// gateway wraps it in this structure to give the contract a typed output.
structure EmbeddingListOutput {
    /// Matching embedding rows.
    @required
    embeddings: EmbeddingRecordList
}

// ── Operations ──────────────────────────────────────────────────────────────
/// Return every stored embedding (vector included) for one entity URI.
///
/// Chunk vectors are addressed as `urn:coa:chunk:<chunkId>`; filtering by
/// `entityType: "chunk"` and `embeddingType: "chunk"` narrows the scan.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/embeddings/by-entity/{entityUri}", code: 200)
@examples([
    {
        title: "Read a chunk's vector"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", entityUri: "urn:coa:chunk:1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d", entityType: "chunk", embeddingType: "chunk" }
        output: {
            embeddings: [
                {
                    id: "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d"
                    ontologyId: "urn:coa:abox:documents"
                    entityUri: "urn:coa:chunk:1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d"
                    entityType: "chunk"
                    embeddingType: "chunk"
                    modelId: "BAAI/bge-m3"
                    dimensions: 1024
                    createdAt: "2026-11-10T08:00:00Z"
                    vector: [0.1, 0.2, 0.3]
                }
            ]
        }
    }
])
operation GetEntityEmbeddings {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Entity URI whose vectors to read.
        @required
        @httpLabel
        @length(min: 1, max: 2048)
        entityUri: String

        /// Only rows written for this entity type.
        @httpQuery("entity_type")
        entityType: EmbeddingEntityType

        /// Only rows of this vector kind.
        @httpQuery("embedding_type")
        embeddingType: EmbeddingType

        /// Only rows produced by this model.
        @httpQuery("model_id")
        modelId: EmbeddingModelId
    }

    output: EmbeddingListOutput
}

/// k-nearest-neighbour search over a namespace's stored vectors.
///
/// The caller supplies the query vector (the web app reuses the vector already
/// stored for a chunk); no embedding is computed server-side.
@http(method: "POST", uri: "/namespaces/{namespaceId}/embeddings/search", code: 200)
@examples([
    {
        title: "Search the five nearest chunk vectors"
        input: {
            namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
            vector: [0.1, 0.2, 0.3]
            entityType: "chunk"
            embeddingType: "chunk"
            modelId: "BAAI/bge-m3"
            topK: 5
        }
        output: {
            embeddings: []
        }
    }
])
operation SearchEmbeddings {
    input := {
        @required
        @httpLabel
        namespaceId: Uuid

        /// Query vector. Must have the same dimensionality as the stored rows.
        @required
        vector: DoubleList

        /// Restrict the search to this vector kind.
        @required
        @jsonName("embedding_type")
        embeddingType: EmbeddingType

        /// Restrict the search to vectors from this model.
        @required
        @jsonName("model_id")
        modelId: EmbeddingModelId

        /// Restrict the search to this entity type (engine default: `class`).
        @jsonName("entity_type")
        entityType: EmbeddingEntityType

        /// Restrict the search to one ontology's named graph.
        @jsonName("ontology_id")
        @length(min: 1, max: 2048)
        ontologyId: String

        /// Number of nearest rows to return (engine default: 10).
        @jsonName("top_k")
        @range(min: 1, max: 100)
        topK: Integer
    }

    output: EmbeddingListOutput
}
