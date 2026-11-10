// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// @examples for com.amazon.semanticcontext.dictionary operations (P4, F58-F66).
// Extracted from the service definition to keep operation/shape definitions
// readable. `apply` merges the @examples trait back onto each operation, so the
// doc-coverage gate in linters.smithy still holds.
$version: "2"

namespace com.amazon.semanticcontext.dictionary

apply ListTerms @examples([
    {
        title: "List the first page of alias entries"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", limit: 100, offset: 0 }
        output: {
            namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
            graph: "https://coa.local/graph/lexicon"
            counts: { anchorClasses: 42, termEntries: 318, evidenced: 261, inferred: 57 }
            entries: [
                {
                    entry: "https://coa.local/term/customer"
                    classIri: "https://coa.local/ontology#Customer"
                    classLabel: "Customer"
                    label: "客户"
                    status: "evidenced"
                    confidence: 0.98
                }
            ]
            total: 318
            offset: 0
            limit: 100
        }
    }
])

apply ListDictionaries @examples([
    {
        title: "List sources that have a dictionary snapshot"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", limit: 50, offset: 0 }
        output: {
            items: [
                {
                    sourceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
                    sourceKind: "postgresql"
                    tables: 12
                    columns: 143
                    commented: 118
                    bound: 96
                    observedAt: "2026-11-10T09:15:00Z"
                }
            ]
            total: 1
            offset: 0
            limit: 50
        }
    }
])

apply GetDictionary @examples([
    {
        title: "Describe one source's dictionary"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d" }
        output: {
            sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d"
            sourceKind: "postgresql"
            catalog: "analytics"
            schema: "public"
            tables: [
                {
                    table: "loan_account"
                    columns: 21
                    commented: 20
                    bound: 18
                    missingComment: 1
                    unbound: 3
                }
            ]
            totals: { total: 21, commented: 20, missing: 1, ratio: 0.952 }
            boundColumns: 18
        }
    }
])

apply GetDictionaryView @examples([
    {
        title: "Page columns that are missing a comment"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d", view: "missing_comment", limit: 50, offset: 0 }
        output: {
            items: [
                {
                    sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d"
                    catalog: "analytics"
                    schema: "public"
                    table: "loan_account"
                    column: "legacy_flag"
                    dataType: "boolean"
                    isNullable: true
                    sourceKind: "postgresql"
                    bindingMethod: "none"
                    observedAt: "2026-11-10T09:15:00Z"
                }
            ]
            total: 1
            offset: 0
            limit: 50
            view: "missing_comment"
            coverage: { total: 21, commented: 20, missing: 1, ratio: 0.952 }
        }
    }
])

apply GetDictionaryCommentCoverage @examples([
    {
        title: "Comment coverage for one source"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d" }
        output: {
            sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d"
            coverage: { total: 143, commented: 118, missing: 25, ratio: 0.825 }
            tables: [
                {
                    table: "loan_account"
                    columns: 21
                    commented: 20
                    bound: 18
                    missingComment: 1
                    unbound: 3
                }
            ]
        }
    }
])

apply RefreshDictionaries @examples([
    {
        title: "Refresh a source's dictionary (idempotent retry)"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d", idempotencyKey: "refresh-20261110-0915", requestedBy: "data-team@example.com" }
        output: {
            run: { runId: "5c1e7a90-2b4f-4d8a-a1c3-7e9f0b2d4c68", sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d", status: "succeeded", idempotencyKey: "refresh-20261110-0915", requestedBy: "data-team@example.com", startedAt: "2026-11-10T09:15:00Z", finishedAt: "2026-11-10T09:15:02Z", processed: 143, inserted: 2, updated: 5, unchanged: 136, removed: 0 }
            bindingBasis: "published-ontology"
        }
    }
])
