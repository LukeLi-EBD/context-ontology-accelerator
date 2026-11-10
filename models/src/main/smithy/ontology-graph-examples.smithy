// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
// @examples for com.amazon.semanticcontext.ontologygraph operations.
// Extracted from the service definition to keep operation/shape
// definitions readable. `apply` merges the @examples trait back onto
// each operation, so the doc-coverage gate in linters.smithy still holds.
$version: "2"

namespace com.amazon.semanticcontext.ontologygraph

apply ListOntologies @examples([
    {
        title: "List induced ontologies in a namespace"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyType: "induced", maxResults: 20 }
        output: {
            ontologies: [
                {
                    ontologyId: "http://coa.amazon.com/onto/sales-crm"
                    uri: "http://coa.amazon.com/onto/sales-crm"
                    title: "Sales CRM"
                    description: "Induced ontology for the CRM sales schema."
                    ontologyType: "induced"
                    format: "text/turtle"
                    domainTags: ["sales", "crm"]
                    classCount: 12
                    propertyCount: 34
                    axiomCount: 210
                    embeddingCount: 46
                    graphUri: "http://coa.amazon.com/onto/sales-crm"
                    createdAt: "2026-07-20T14:03:11Z"
                    updatedAt: "2026-07-21T09:15:42Z"
                }
            ]
        }
    }
])

apply GetOntology @examples([
    {
        title: "Get an ontology by ID"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "01J9ZQ8XN4T7VBR6C2K9YHMED0" }
        output: {
            ontology: { ontologyId: "http://coa.amazon.com/onto/sales-crm", uri: "http://coa.amazon.com/onto/sales-crm", title: "Sales CRM", ontologyType: "induced", classCount: 12 }
        }
    }
])

apply DeleteOntology @examples([
    {
        title: "Delete an induced ontology (async, 202)"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "http://coa.amazon.com/onto/sales-crm" }
        output: {}
    }
])

apply UploadOntology @examples([
    {
        title: "Upload a Turtle ontology file"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "sales-crm", body: "QHByZWZpeCBleDogPGh0dHA6Ly9leGFtcGxlLmNvbS9vbnRvIz4gLgpleDpDdXN0b21lciBhIG93bDpDbGFzcyAuCg==" }
        output: {
            result: { ontologyId: "sales-crm", classCount: 12, status: "uploaded" }
        }
    }
])

apply DownloadOntology @examples([
    {
        title: "Download an ontology as Turtle"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "sales-crm" }
        output: { downloadUrl: "https://coa-artifacts.s3.amazonaws.com/downloads/sales-analytics/sales-crm.ttl?X-Amz-Signature=abc123", expiresInSeconds: 3600 }
    }
])

apply FetchOntology @examples([
    {
        title: "Fetch a foundational ontology from a URL"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "foaf", sourceUrl: "https://xmlns.com/foaf/spec/index.rdf" }
        output: {
            result: { ontologyId: "foaf", classCount: 13, status: "ingested" }
        }
    }
])

apply GetOntologyUploadUrl @examples([
    {
        title: "Get a presigned upload URL for an ontology file"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", filename: "sales-crm.ttl", contentType: "text/turtle", ontologyId: "sales-crm", title: "Sales CRM" }
        output: { uploadUrl: "https://coa-uploads.s3.amazonaws.com/sales-analytics/sales-crm.ttl?X-Amz-Signature=abc123", s3Key: "uploads/sales-analytics/sales-crm.ttl", ontologyId: "sales-crm" }
    }
])

apply IngestOntologyFromS3 @examples([
    {
        title: "Kick off an async ingest from S3"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "sales-crm", s3Key: "uploads/sales-analytics/sales-crm.ttl", format: "turtle", title: "Sales CRM", ontologyType: "induced" }
        output: {
            result: { jobId: "01J9ZQ8XN4T7VBR6C2K9YHMED0", ontologyId: "sales-crm", status: "pending" }
        }
    }
])

apply GetIngestStatus @examples([
    {
        title: "Poll a completed ingest job"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "sales-crm", jobId: "01J9ZQ8XN4T7VBR6C2K9YHMED0" }
        output: {
            result: {
                jobId: "01J9ZQ8XN4T7VBR6C2K9YHMED0"
                ontologyId: "sales-crm"
                status: "completed"
                result: { ontologyId: "sales-crm", classCount: 12, embeddingCount: 46 }
            }
        }
    }
])

apply GraphSearch @examples([
    {
        title: "Search for class vertices matching a term"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", q: "customer", kind: "class", limit: 10, offset: 0 }
        output: {
            hits: [
                {
                    uri: "http://example.com/onto#Customer"
                    label: "Customer"
                    kind: "class"
                    graphUris: ["http://coa.amazon.com/onto/sales-crm"]
                }
            ]
            totalCount: 1
        }
    }
])

apply GetGraphClass @examples([
    {
        title: "Look up a class vertex by IRI"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", uri: "http://example.com/onto#Customer" }
        output: {
            uri: "http://example.com/onto#Customer"
            kind: "class"
            namespace: "sales-analytics"
            types: ["http://www.w3.org/2002/07/owl#Class"]
            labels: ["Customer"]
            comments: ["A party that purchases goods or services."]
            altLabels: ["Client", "Account"]
            graphUris: ["http://coa.amazon.com/onto/sales-crm"]
            isMapped: true
            edges: [
                {
                    predicate: "http://example.com/onto#placedOrder"
                    predicateLabel: "placed order"
                    direction: "outbound"
                    neighbor: { uri: "http://example.com/onto#Order", label: "Order", kind: "class" }
                }
            ]
        }
    }
])

apply GetGraphObjectProperty @examples([
    {
        title: "Look up an object-property vertex by IRI"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", uri: "http://example.com/onto#placedOrder" }
        output: {
            uri: "http://example.com/onto#placedOrder"
            kind: "object-property"
            namespace: "sales-analytics"
            types: ["http://www.w3.org/2002/07/owl#ObjectProperty"]
            labels: ["placed order"]
            graphUris: ["http://coa.amazon.com/onto/sales-crm"]
            edges: [
                {
                    predicate: "http://www.w3.org/2000/01/rdf-schema#domain"
                    direction: "outbound"
                    neighbor: { uri: "http://example.com/onto#Customer", label: "Customer", kind: "class" }
                }
            ]
        }
    }
])

apply GetGraphDatatypeProperty @examples([
    {
        title: "Look up a datatype-property vertex by IRI"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", uri: "http://example.com/onto#emailAddress" }
        output: {
            uri: "http://example.com/onto#emailAddress"
            kind: "datatype-property"
            namespace: "sales-analytics"
            types: ["http://www.w3.org/2002/07/owl#DatatypeProperty"]
            labels: ["email address"]
            graphUris: ["http://coa.amazon.com/onto/sales-crm"]
            edges: [
                {
                    predicate: "http://www.w3.org/2000/01/rdf-schema#range"
                    direction: "outbound"
                    neighbor: { uri: "http://www.w3.org/2001/XMLSchema#string", kind: "literal" }
                }
            ]
        }
    }
])

apply GetOntologyOverview @examples([
    {
        title: "Enumerate the classes and properties in an ontology's graph"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", ontologyId: "http://coa.amazon.com/onto/sales-crm" }
        output: {
            ontologyId: "http://coa.amazon.com/onto/sales-crm"
            namespace: "sales-analytics"
            graphUri: "http://coa.amazon.com/onto/sales-crm"
            classes: [
                {
                    uri: "http://example.com/onto#Customer"
                    label: "Customer"
                    comment: "A party that purchases goods or services."
                    groundedTo: "urn:coa:class:Party"
                    matchType: "close"
                }
            ]
            objectProperties: [
                {
                    uri: "http://example.com/onto#placedOrder"
                    label: "placed order"
                    domain: "http://example.com/onto#Customer"
                    range: "http://example.com/onto#Order"
                }
            ]
            datatypeProperties: [
                {
                    uri: "http://example.com/onto#emailAddress"
                    label: "email address"
                    domain: "http://example.com/onto#Customer"
                    range: "http://www.w3.org/2001/XMLSchema#string"
                }
            ]
            totalClasses: 1
            totalObjectProperties: 1
            totalDatatypeProperties: 1
        }
    }
])

apply ListStatements @examples([
    {
        title: "List the statements that mention one subject"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", subject: "http://example.com/onto#Customer", limit: 2 }
        output: {
            statements: [
                {
                    graph: "http://coa.amazon.com/onto/sales-crm"
                    subject: "http://example.com/onto#Customer"
                    predicate: "http://www.w3.org/2000/01/rdf-schema#label"
                    object: "Customer"
                }
                {
                    graph: "http://coa.amazon.com/onto/sales-crm"
                    subject: "http://example.com/onto#Customer"
                    predicate: "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                    object: "http://www.w3.org/2002/07/owl#Class"
                }
            ]
            truncated: false
        }
    }
])

apply GetCanvasManifest @examples([
    {
        title: "Read the canvas capabilities and limits"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" }
        output: {
            capabilities: ["nodeKinds", "graphFilter", "offsetPaging"]
            limits: { maxNodes: 200, maxEdges: 400, maxPageSize: 100 }
        }
    }
])

apply GetCanvasSubgraph @examples([
    {
        title: "List the first page of every kind"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", limit: 2, offset: 0 }
        output: {
            nodes: [
                {
                    uri: "http://example.com/onto#Customer"
                    label: "Customer"
                    kind: "class"
                }
                {
                    uri: "http://example.com/onto#Place"
                    label: "Place"
                    kind: "class"
                }
            ]
            edges: [
                {
                    source: "http://example.com/onto#Customer"
                    predicate: "http://www.w3.org/2000/01/rdf-schema#subClassOf"
                    predicateLabel: "subClassOf"
                    target: "http://example.com/onto#Place"
                    graph: "http://coa.amazon.com/onto/sales-crm"
                    direction: "outgoing"
                }
            ]
            truncated: true
            nodeCount: 2
            edgeCount: 1
            nextOffset: 2
        }
    }
    {
        title: "Filter one named graph to classes only"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", kinds: "class", graph: "http://coa.amazon.com/onto/sales-crm", limit: 50, offset: 0 }
        output: {
            nodes: [
                {
                    uri: "http://example.com/onto#Customer"
                    label: "Customer"
                    kind: "class"
                }
            ]
            edges: []
            truncated: false
            nodeCount: 1
            edgeCount: 0
        }
    }
])

apply GetOntologySnapshot @examples([
    {
        title: "Read T-Box/A-Box coverage for a namespace"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" }
        output: {
            tbox: { classes: 156, objectProperties: 84, datatypeProperties: 45 }
            abox: { instances: 18020, classesWithInstances: 4 }
            coverage: { classCoverage: 0.0256, unlabeledClasses: 0 }
            graphs: ["http://coa.amazon.com/onto/sales-crm", "urn:coa:abox:platform-synthetic"]
            source: "SPARQL aggregation over the namespace named graphs"
            sampledAt: "2026-11-10T09:00:00Z"
        }
    }
])

apply RunValidation @examples([
    {
        title: "Run the read-only quality checks"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" }
        output: {
            orphanInstances: { count: 0, detail: "instances typed by a declared class with no other edge" }
            unlabeledClasses: { count: 0, detail: "declared classes missing rdfs:label and skos:prefLabel" }
            shacl: { status: "skipped", detail: "no shapes configured (no-shapes)" }
            inferenceFailures: { detail: "no reasoner wired up in this deployment" }
            source: "SPARQL over the namespace named graphs; SHACL shapes from the configured shapes file"
            sampledAt: "2026-11-10T09:00:00Z"
        }
    }
])

apply GetReasoningStatus @examples([
    {
        title: "No reasoner configured"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" }
        output: {
            available: false
            failures: { detail: "inference jobs are not observable from this service" }
            detail: "This deployment does not configure a reasoner; only asserted triples are served."
            source: "ontology-engine capability check"
            sampledAt: "2026-11-10T09:00:00Z"
        }
    }
])

apply GetOntologyDiff @examples([
    {
        title: "Diff a baseline graph against a newer one"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", fromGraph: "http://coa.amazon.com/onto/sales-crm-v1", toGraph: "http://coa.amazon.com/onto/sales-crm-v2", limit: 20 }
        output: {
            baselineGraph: "http://coa.amazon.com/onto/sales-crm-v1"
            targetGraph: "http://coa.amazon.com/onto/sales-crm-v2"
            counts: { addedTriples: 12, removedTriples: 3, addedClasses: 1, removedClasses: 0, addedProperties: 2, removedProperties: 1 }
            addedClasses: ["http://example.com/onto#LoyaltyAccount"]
            removedClasses: []
            addedProperties: ["http://example.com/onto#loyaltyTier"]
            removedProperties: ["http://example.com/onto#legacyCode"]
            examples: {
                addedTriples: [
                    {
                        subject: "http://example.com/onto#LoyaltyAccount"
                        predicate: "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                        object: "http://www.w3.org/2002/07/owl#Class"
                    }
                ]
                removedTriples: []
            }
            truncated: false
            source: "SPARQL MINUS over the two named graphs"
            sampledAt: "2026-11-10T09:00:00Z"
        }
    }
])

apply FindGraphPath @examples([
    {
        title: "Find paths from a customer to a place"
        input: { namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", start: "http://example.com/onto#Customer", end: "http://example.com/onto#Place", maxHops: 3, limit: 5 }
        output: {
            paths: [
                {
                    nodes: [
                        {
                            uri: "http://example.com/onto#Customer"
                            label: "Customer"
                            kind: "class"
                        }
                        {
                            uri: "http://example.com/onto#Place"
                            label: "Place"
                            kind: "class"
                        }
                    ]
                    edges: [
                        {
                            source: "http://example.com/onto#Customer"
                            predicate: "http://www.w3.org/2000/01/rdf-schema#subClassOf"
                            predicateLabel: "subClassOf"
                            target: "http://example.com/onto#Place"
                            graph: "http://coa.amazon.com/onto/sales-crm"
                            direction: "outgoing"
                        }
                    ]
                    hops: 1
                }
            ]
            truncated: false
        }
    }
])
