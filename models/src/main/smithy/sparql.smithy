// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
//
// SPARQL console (P6 F72–F74) — self-contained shapes and one operation.
//
// MERGE NOTE — when this file reaches the mainline, append exactly this line to
// the end of the `operations: [...]` list of `service DataLayerService` in
// `models/src/main/smithy/data-layer.smithy`, after the last existing entry
// (the list order carries no meaning):
//
//     RunSparql
//
// No other shared Smithy file needs to change. The operation, its input/output,
// its errors and its example all live in this file; `NamespaceNotFoundError` is
// reused from serve.smithy, which declares the same namespace.
$version: "2"

namespace com.amazon.semanticcontext.datalayer

// ══════════════════════════════════════════════════════════════════════════════
// RunSparql
// ══════════════════════════════════════════════════════════════════════════════
/// Runs one SPARQL SELECT or ASK in the SPARQL console.
///
/// The query is confined to the namespace's own graphs: they form the default
/// graph and each stays addressable as a named graph. The statement is refused
/// when it carries `FROM` / `FROM NAMED`, uses `SERVICE` or `LOAD`, names a graph
/// outside the namespace, is not SELECT/ASK, runs longer than 10 seconds, or
/// produces more than 4 MiB. At most 5,000 rows are returned; `truncated` says
/// whether the provider produced more.
@readonly
@http(method: "POST", uri: "/namespaces/{namespaceId}/sparql", code: 200)
@examples([
    {
        title: "List five subjects in the namespace"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", sparql: "SELECT ?s WHERE { ?s ?p ?o } LIMIT 5" }
        output: {
            form: "SELECT"
            variables: ["s"]
            rows: [
                ["https://coa.local/entity/customer-42"]
            ]
            rowCount: 1
            returnedRows: 1
            truncated: false
            graphCount: 2
            elapsedMs: 37
        }
    }
    {
        title: "Ask whether any triple exists"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", sparql: "ASK { ?s ?p ?o }" }
        output: { form: "ASK", answer: true, rowCount: 0, returnedRows: 0, truncated: false, graphCount: 2, elapsedMs: 12 }
    }
])
operation RunSparql {
    input: RunSparqlInput
    output: RunSparqlOutput
    errors: [
        NamespaceNotFoundError
        SparqlBadRequestError
        SparqlResultTooLargeError
        SparqlQuotaExceededError
        SparqlProviderError
        SparqlScopeTooLargeError
        SparqlTimeoutError
    ]
}

/// The namespace and the statement to run.
structure RunSparqlInput {
    /// The namespace whose graphs the query may read.
    @required
    @httpLabel
    @length(min: 1, max: 128)
    namespaceId: String

    /// SPARQL text: one SELECT or ASK statement.
    @required
    @length(min: 1, max: 6000)
    sparql: String
}

/// One executed statement: its form, the ASK answer, or the SELECT columns and rows.
structure RunSparqlOutput {
    /// The executed form: `SELECT` or `ASK`.
    @required
    form: String

    /// The ASK answer; present only when `form` is `ASK`.
    answer: Boolean

    /// Column names, in the provider's order (SELECT only).
    variables: SparqlVariableList

    /// Rows, each aligned to `variables` (SELECT only).
    rows: SparqlRowList

    /// Rows the provider produced before the 5,000-row display cap (SELECT only).
    @required
    rowCount: Integer

    /// Rows actually returned in `rows` (SELECT only; at most 5,000).
    @required
    returnedRows: Integer

    /// True when the provider produced more than 5,000 rows and `rows` was cut.
    @required
    truncated: Boolean

    /// Number of namespace graphs the query was confined to.
    @required
    graphCount: Integer

    /// Server-side execution time in milliseconds.
    elapsedMs: Integer
}

/// Column names of a SELECT result, in provider order.
list SparqlVariableList {
    /// One variable name, without the leading `?`.
    member: String
}

/// One result row; each value is an RDF term rendered for display.
list SparqlRow {
    /// One RDF term: an IRI as-is, a literal with its language/datatype suffix,
    /// or a blank node as `_:id`.
    member: String
}

/// All returned rows, at most 5,000.
list SparqlRowList {
    /// One result row aligned to `variables`.
    member: SparqlRow
}

// ══════════════════════════════════════════════════════════════════════════════
// Errors
// ══════════════════════════════════════════════════════════════════════════════
/// The statement was refused before execution: syntax, form, dataset clause,
/// federation, `LOAD`, length, or a graph outside the namespace.
@error("client")
@httpError(400)
structure SparqlBadRequestError {
    /// Human-readable description of the refusal.
    @required
    message: String

    /// Stable machine code, e.g. `E_SPARQL_SYNTAX` or `E_SPARQL_FEDERATED`.
    @required
    code: String

    /// The provider's own code when the refusal came from the provider.
    providerCode: String

    /// The provider's own message, truncated for display.
    providerMessage: String
}

/// The result exceeded the 4 MiB response cap.
@error("client")
@httpError(413)
structure SparqlResultTooLargeError {
    /// Human-readable description of the size refusal.
    @required
    message: String

    /// Stable machine code: `E_SPARQL_RESULT_TOO_LARGE`.
    @required
    code: String
}

/// The caller exceeded the console quota.
@error("client")
@httpError(429)
structure SparqlQuotaExceededError {
    /// Human-readable description of the quota refusal.
    @required
    message: String

    /// Stable machine code: `E_SPARQL_QUOTA_EXCEEDED`.
    @required
    code: String
}

/// The provider could not execute the statement.
@error("server")
@httpError(502)
structure SparqlProviderError {
    /// Human-readable description of the provider failure.
    @required
    message: String

    /// Stable machine code: `E_SPARQL_PROVIDER_ERROR` or `E_SPARQL_PROVIDER_REJECTED`.
    @required
    code: String

    /// The provider's own code, e.g. `HTTP_400`.
    providerCode: String

    /// The provider's own message, truncated for display.
    providerMessage: String
}

/// The namespace needs more graphs than the console admits.
@error("server")
@httpError(503)
structure SparqlScopeTooLargeError {
    /// Human-readable description of the scope refusal.
    @required
    message: String

    /// Stable machine code: `E_SPARQL_SCOPE_TOO_LARGE` or `E_SPARQL_SCOPE_EMPTY`.
    @required
    code: String
}

/// The statement exceeded the 10 second limit.
@error("server")
@httpError(504)
structure SparqlTimeoutError {
    /// Human-readable description of the timeout.
    @required
    message: String

    /// Stable machine code: `E_SPARQL_TIMEOUT`.
    @required
    code: String
}
