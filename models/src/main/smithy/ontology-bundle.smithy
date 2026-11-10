// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// Governance bundle migration: export a deployment snapshot, inspect a bundle
// on disk, and import it into a restore database.
//
// Spec: doc/coa-x/09-platform整合评估.md §5.6 rows F118-F120 and
// doc/coa-x/18-platform-core拆解.md §KERNEL governance routes. The bridge
// forwards these to `platform_core.bundle`; keeping them in the contract is
// what lets the bundle path survive the platform-core split.
$version: "2"

namespace com.amazon.semanticcontext.ontologybundle

use com.amazon.semanticcontext.common#NotFoundError
use com.amazon.semanticcontext.common#OntologyId
use com.amazon.semanticcontext.common#Uuid
use com.amazon.semanticcontext.common#ValidationError
use com.amazon.semanticcontext.ontologylifecycle#OntologyPointer

/// Directory or bundle path. Absolute paths are resolved by the server.
@length(min: 1, max: 2048)
string BundlePath

/// Bundle tag, used in the manifest and the default directory name.
@length(min: 1, max: 128)
string BundleTag

/// Restore database name; the server refuses the production database.
@length(min: 1, max: 128)
string BundleDatabaseName

/// Identity performing the bundle operation.
@length(min: 1, max: 256)
string BundleActor

/// Counters recorded in a bundle manifest. Values are numbers or nested maps,
/// so they stay free-form rather than being flattened into fixed fields.
map BundleTotals {
    /// Counter name, e.g. `documents` or `tripleBreakdown`.
    key: String

    /// Counter value.
    value: Document
}

/// T-Box coordinates recorded by an import.
structure BundleTboxRestored {
    /// Version the bundle registered.
    versionId: String

    /// Canonical hash of the restored graph.
    contentHash: String

    /// Graph IRI the bundle was loaded into.
    graph: String
}

/// One post-import consistency check.
structure BundleCheck {
    /// Check name, e.g. `documents` or `vectors`.
    @required
    name: String

    /// Value recorded in the manifest.
    exported: Document

    /// Value observed in the restored database.
    imported: Document

    /// True when the two values agree.
    @required
    ok: Boolean

    /// Explanation when the check failed.
    detail: String
}

/// Ledger counters and chain verdict after an import.
structure BundleLedger {
    /// Fact events restored.
    events: Integer

    /// Fact assertions restored.
    facts: Integer

    /// True when the restored fact-event chain verifies.
    chain: Boolean
}

/// Blob-store outcome after an import.
structure BundleBlobs {
    /// True when the bundle carried blobs.
    included: Boolean

    /// Blobs present in the bundle.
    count: Integer

    /// Total blob bytes.
    bytes: Long

    /// Blobs written into the restore target.
    written: Integer

    /// Blobs that already existed in the target.
    existing: Integer
}

/// Checks in a bundle import response.
list BundleCheckList {
    member: BundleCheck
}

/// Result of `ExportOntologyBundle`.
structure OntologyBundleExportResult {
    /// Always true on success.
    @required
    ok: Boolean

    /// Absolute directory the bundle was written to.
    @required
    bundleDir: String

    /// Tag recorded in the manifest.
    @required
    tag: String

    /// Manifest schema version.
    schemaVersion: Integer

    /// Manifest generation time (ISO-8601).
    generatedAt: String

    /// T-Box coordinates captured by the bundle.
    tbox: Document

    /// Row counts captured by the bundle.
    totals: BundleTotals

    /// Total bytes written.
    bytes: Long

    /// Number of files written.
    files: Integer

    /// Identity that ran the export.
    actor: String
}

/// Result of `InspectOntologyBundle`.
structure OntologyBundleInspectResult {
    /// Always true when the manifest verifies.
    @required
    ok: Boolean

    /// Path that was inspected.
    @required
    path: String

    /// Tag recorded in the manifest.
    tag: String

    /// Row counts recorded in the manifest.
    totals: BundleTotals

    /// T-Box coordinates recorded in the manifest.
    tbox: Document

    /// Number of files in the bundle.
    files: Integer
}

/// Result of `ImportBundle`.
structure OntologyBundleImportResult {
    /// True when every restored check agrees.
    ok: Boolean

    /// Restore database the bundle was loaded into.
    database: String

    /// Bundle directory that was imported.
    bundle: String

    /// T-Box coordinates registered by the import.
    tbox: BundleTboxRestored

    /// Pointer state after the T-Box restore.
    tboxPointer: OntologyPointer

    /// A-Box graph the bundle was loaded into.
    aboxGraph: String

    /// Post-import consistency checks.
    checks: BundleCheckList

    /// Ledger counters and chain verdict.
    ledger: BundleLedger

    /// Blob-store outcome.
    blobs: BundleBlobs

    /// Expected row counts from the manifest.
    counts: Document

    /// Step that failed, when `ok` is false.
    failedStep: String

    /// Failure message, when `ok` is false.
    error: String

    /// Provider error code, when `ok` is false.
    providerCode: String

    /// Identity that ran the import.
    actor: String
}

/// Export a deployment snapshot into a bundle directory.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/export", code: 200)
@examples([
    {
        title: "Export a bundle with blobs"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", tag: "release-2026-11", includeBlobs: true }
        output: { ok: true, bundleDir: "/data/bundles/release-2026-11", tag: "release-2026-11", schemaVersion: 3, bytes: 1048576, files: 42 }
    }
])
operation ExportOntologyBundle {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Output directory; the server default when omitted.
        out: BundlePath

        /// Bundle tag; a generated tag when omitted.
        tag: BundleTag

        /// Include the A-Box blob store in the bundle.
        includeBlobs: Boolean

        /// Who runs the export.
        actor: BundleActor
    }

    output: OntologyBundleExportResult

    errors: [
        ValidationError
        NotFoundError
    ]
}

/// Inspect a bundle's manifest without restoring it.
@readonly
@http(method: "GET", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/inspect", code: 200)
@examples([
    {
        title: "Inspect a bundle on disk"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", bundleRef: "/data/bundles/release-2026-11" }
        output: { ok: true, path: "/data/bundles/release-2026-11", tag: "release-2026-11", totals: { documents: 12, triples: 4200 }, files: 42 }
    }
])
operation InspectOntologyBundle {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Bundle directory to inspect.
        @required
        @httpQuery("bundleRef")
        bundleRef: BundlePath
    }

    output: OntologyBundleInspectResult

    errors: [
        ValidationError
        NotFoundError
    ]
}

/// Restore a bundle into a non-production database.
@http(method: "POST", uri: "/namespaces/{namespaceId}/ontologies/{ontologyId}/bundles/import", code: 200)
@examples([
    {
        title: "Restore a bundle into a test database"
        input: { namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11", ontologyId: "https://example.com/ontology/core", bundleRef: "/data/bundles/release-2026-11", database: "platform_restore_test", replace: false, actor: "operator" }
        output: { ok: true, database: "platform_restore_test", bundle: "/data/bundles/release-2026-11", tbox: { versionId: "ont-1a2b3c4d5e6f", graph: "urn:platform:graph:tbox:1a2b3c4d" }, ledger: { events: 41, facts: 1280, chain: true } }
    }
])
operation ImportBundle {
    input := {
        /// Namespace that owns the ontology.
        @required
        @httpLabel
        namespaceId: Uuid

        /// Ontology identifier.
        @required
        @httpLabel
        ontologyId: OntologyId

        /// Bundle directory to restore.
        @required
        bundleRef: BundlePath

        /// Restore database; defaults to `platform_restore_test` when omitted.
        database: BundleDatabaseName

        /// Drop and recreate the restore database before loading.
        replace: Boolean

        /// Keep the restore database when a step fails, for inspection.
        keepDbOnFailure: Boolean

        /// Who runs the restore.
        actor: BundleActor
    }

    output: OntologyBundleImportResult

    errors: [
        ValidationError
        NotFoundError
    ]
}
