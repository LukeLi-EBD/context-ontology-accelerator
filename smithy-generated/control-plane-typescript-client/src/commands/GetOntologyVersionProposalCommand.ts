// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  ControlPlaneServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../ControlPlaneServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { GetOntologyVersionProposalInput, OntologyProposalDetail } from "../models/models_1";
import { GetOntologyVersionProposal$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologyVersionProposalCommand}.
 */
export interface GetOntologyVersionProposalCommandInput extends GetOntologyVersionProposalInput {}
/**
 * @public
 *
 * The output of {@link GetOntologyVersionProposalCommand}.
 */
export interface GetOntologyVersionProposalCommandOutput extends OntologyProposalDetail, __MetadataBearer {}

/**
 * Read one proposal with its version and stored diff.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologyVersionProposalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologyVersionProposalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologyVersionProposalInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 * };
 * const command = new GetOntologyVersionProposalCommand(input);
 * const response = await client.send(command);
 * // { // OntologyProposalDetail
 * //   proposal: { // OntologyProposal
 * //     proposalId: "STRING_VALUE", // required
 * //     versionId: "STRING_VALUE", // required
 * //     againstVersion: "STRING_VALUE",
 * //     changeSummary: "STRING_VALUE",
 * //     status: "proposed" || "review" || "approved" || "published" || "rejected", // required
 * //     breaking: true || false, // required
 * //     acknowledgedBreaking: true || false,
 * //     diff: { // OntologyDiff
 * //       from: "STRING_VALUE",
 * //       to: "STRING_VALUE", // required
 * //       breaking: true || false, // required
 * //       breakingItems: [ // OntologyBreakingItemList // required
 * //         { // OntologyBreakingItem
 * //           kind: "STRING_VALUE", // required
 * //           iri: "STRING_VALUE",
 * //           property: "STRING_VALUE",
 * //           from: [ // OntologyStringList
 * //             "STRING_VALUE",
 * //           ],
 * //           to: [
 * //             "STRING_VALUE",
 * //           ],
 * //         },
 * //       ],
 * //       summary: { // OntologyDiffSummary
 * //         addedTriples: Number("int"), // required
 * //         removedTriples: Number("int"), // required
 * //         addedClasses: [ // required
 * //           "STRING_VALUE",
 * //         ],
 * //         removedClasses: [ // required
 * //           "STRING_VALUE",
 * //         ],
 * //         addedProperties: [ // required
 * //           "STRING_VALUE",
 * //         ],
 * //         removedProperties: "<OntologyStringList>", // required
 * //         domainChanges: [ // OntologyDomainChangeList // required
 * //           { // OntologyDomainChange
 * //             property: "STRING_VALUE", // required
 * //             from: "<OntologyStringList>", // required
 * //             to: "<OntologyStringList>", // required
 * //           },
 * //         ],
 * //         rangeChanges: [ // required
 * //           {
 * //             property: "STRING_VALUE", // required
 * //             from: "<OntologyStringList>", // required
 * //             to: "<OntologyStringList>", // required
 * //           },
 * //         ],
 * //         removedClassInstances: [ // OntologyClassInstanceList // required
 * //           { // OntologyClassInstance
 * //             class: "STRING_VALUE", // required
 * //             instances: Number("int"), // required
 * //           },
 * //         ],
 * //       },
 * //       markdown: "STRING_VALUE",
 * //     },
 * //     impact: { // OntologyImpact
 * //       addedTriples: Number("int"),
 * //       removedTriples: Number("int"),
 * //       addedClasses: Number("int"),
 * //       removedClasses: Number("int"),
 * //       addedProperties: Number("int"),
 * //       removedProperties: Number("int"),
 * //       domainChanges: Number("int"),
 * //       rangeChanges: Number("int"),
 * //       removedClassInstances: Number("int"),
 * //       breakingItems: Number("int"),
 * //       analysis: { // OntologyImpactAnalysis
 * //         from: "STRING_VALUE",
 * //         to: "STRING_VALUE", // required
 * //         changeSet: { // OntologyImpactChangeSet
 * //           counts: { // OntologyImpactCounts
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //             addedClasses: Number("int"), // required
 * //             removedClasses: Number("int"), // required
 * //             addedProperties: Number("int"), // required
 * //             removedProperties: Number("int"), // required
 * //             domainChanges: Number("int"), // required
 * //             rangeChanges: Number("int"), // required
 * //           },
 * //           addedClasses: "<OntologyStringList>", // required
 * //           removedClasses: "<OntologyStringList>", // required
 * //           addedProperties: "<OntologyStringList>", // required
 * //           removedProperties: "<OntologyStringList>", // required
 * //           domainChanges: [ // required
 * //             {
 * //               property: "STRING_VALUE", // required
 * //               from: "<OntologyStringList>", // required
 * //               to: "<OntologyStringList>", // required
 * //             },
 * //           ],
 * //           rangeChanges: [ // required
 * //             {
 * //               property: "STRING_VALUE", // required
 * //               from: "<OntologyStringList>", // required
 * //               to: "<OntologyStringList>", // required
 * //             },
 * //           ],
 * //           breaking: true || false, // required
 * //           breakingItems: [ // required
 * //             {
 * //               kind: "STRING_VALUE", // required
 * //               iri: "STRING_VALUE",
 * //               property: "STRING_VALUE",
 * //               from: "<OntologyStringList>",
 * //               to: "<OntologyStringList>",
 * //             },
 * //           ],
 * //         },
 * //         affected: { // OntologyImpactAffected
 * //           classes: [ // OntologyImpactClassList // required
 * //             { // OntologyImpactClass
 * //               iri: "STRING_VALUE", // required
 * //               label: "STRING_VALUE", // required
 * //               change: "added" || "removed" || "modified", // required
 * //               addedTriples: Number("int"), // required
 * //               removedTriples: Number("int"), // required
 * //             },
 * //           ],
 * //           properties: [ // OntologyImpactPropertyList // required
 * //             { // OntologyImpactProperty
 * //               iri: "STRING_VALUE", // required
 * //               label: "STRING_VALUE", // required
 * //               change: "added" || "removed" || "modified", // required
 * //               addedTriples: Number("int"), // required
 * //               removedTriples: Number("int"), // required
 * //               domainChanges: "<OntologyDomainChangeList>", // required
 * //               rangeChanges: "<OntologyDomainChangeList>", // required
 * //             },
 * //           ],
 * //           instances: { // OntologyImpactInstances
 * //             total: Number("int"),
 * //             byClass: [ // OntologyImpactClassInstanceList // required
 * //               { // OntologyImpactClassInstances
 * //                 iri: "STRING_VALUE", // required
 * //                 label: "STRING_VALUE", // required
 * //                 instances: Number("int"),
 * //               },
 * //             ],
 * //             source: "STRING_VALUE",
 * //             note: "STRING_VALUE",
 * //             affectedInstances: Number("int"),
 * //             graphs: "<OntologyStringList>",
 * //           },
 * //         },
 * //         aggregations: { // OntologyImpactAggregations
 * //           byClass: [ // OntologyImpactAggregationList // required
 * //             { // OntologyImpactAggregation
 * //               iri: "STRING_VALUE", // required
 * //               label: "STRING_VALUE", // required
 * //               addedTriples: Number("int"), // required
 * //               removedTriples: Number("int"), // required
 * //             },
 * //           ],
 * //           byProperty: [ // required
 * //             {
 * //               iri: "STRING_VALUE", // required
 * //               label: "STRING_VALUE", // required
 * //               addedTriples: Number("int"), // required
 * //               removedTriples: Number("int"), // required
 * //             },
 * //           ],
 * //           unclassified: { // OntologyImpactTripleCount
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //           },
 * //           empty: true || false, // required
 * //           emptyReason: "STRING_VALUE",
 * //           method: "STRING_VALUE",
 * //           rowLimit: Number("int"),
 * //         },
 * //         dependencies: { // OntologyImpactDependencies
 * //           metrics: [ // OntologyImpactMetricList // required
 * //             { // OntologyImpactMetric
 * //               metricId: "STRING_VALUE", // required
 * //               name: "STRING_VALUE",
 * //               matchedBy: "<OntologyStringList>", // required
 * //               source: "STRING_VALUE", // required
 * //             },
 * //           ],
 * //           rules: [ // OntologyImpactRuleList // required
 * //             { // OntologyImpactRule
 * //               metricId: "STRING_VALUE", // required
 * //               ruleId: "STRING_VALUE",
 * //               level: "STRING_VALUE",
 * //               matchedBy: "STRING_VALUE", // required
 * //               source: "STRING_VALUE", // required
 * //             },
 * //           ],
 * //           terms: [ // OntologyImpactTermList // required
 * //             { // OntologyImpactTerm
 * //               surface: "STRING_VALUE",
 * //               canonical: "STRING_VALUE",
 * //               lang: "STRING_VALUE",
 * //               source: "STRING_VALUE",
 * //               canonicalLabel: "STRING_VALUE",
 * //             },
 * //           ],
 * //           notes: [ // OntologyImpactNoteList // required
 * //             { // OntologyImpactNote
 * //               source: "STRING_VALUE", // required
 * //               error: "STRING_VALUE", // required
 * //             },
 * //           ],
 * //           empty: true || false, // required
 * //           emptyReason: "STRING_VALUE",
 * //           method: "STRING_VALUE",
 * //         },
 * //         verification: { // OntologyImpactVerification
 * //           sampled: [ // OntologyImpactSampleList // required
 * //             { // OntologyImpactSample
 * //               iri: "STRING_VALUE", // required
 * //               listed: Number("int"), // required
 * //               recounted: Number("int"), // required
 * //               consistent: true || false, // required
 * //             },
 * //           ],
 * //           consistent: true || false,
 * //           reason: "STRING_VALUE",
 * //           source: "STRING_VALUE",
 * //         },
 * //         inputs: { // OntologyImpactInputs
 * //           from: { // OntologyImpactVersionRef
 * //             versionId: "STRING_VALUE",
 * //             semver: "STRING_VALUE",
 * //             contentHash: "STRING_VALUE",
 * //             tripleCount: Number("int"),
 * //           },
 * //           to: {
 * //             versionId: "STRING_VALUE",
 * //             semver: "STRING_VALUE",
 * //             contentHash: "STRING_VALUE",
 * //             tripleCount: Number("int"),
 * //           },
 * //         },
 * //         inputsFingerprint: "STRING_VALUE",
 * //         empty: true || false, // required
 * //         emptyReason: "STRING_VALUE",
 * //         computedAt: "STRING_VALUE", // required
 * //         source: "STRING_VALUE", // required
 * //         readOnly: true || false, // required
 * //       },
 * //       analysisError: { // OntologyImpactError
 * //         code: "STRING_VALUE", // required
 * //         message: "STRING_VALUE", // required
 * //         details: "DOCUMENT_VALUE",
 * //       },
 * //     },
 * //     createdBy: "STRING_VALUE",
 * //     createdAt: "STRING_VALUE",
 * //     approvedBy: "STRING_VALUE",
 * //     approvedAt: "STRING_VALUE",
 * //     publishedAt: "STRING_VALUE",
 * //     versionStatus: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated",
 * //   },
 * //   version: { // OntologyVersion
 * //     id: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE", // required
 * //     status: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated", // required
 * //     contentHash: "STRING_VALUE",
 * //     tripleCount: Number("int"),
 * //     format: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     rollbackOf: "STRING_VALUE",
 * //     label: "STRING_VALUE",
 * //     createdAt: "STRING_VALUE",
 * //     publishedAt: "STRING_VALUE",
 * //   },
 * //   versionStatus: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated", // required
 * //   diff: {
 * //     from: "STRING_VALUE",
 * //     to: "STRING_VALUE", // required
 * //     breaking: true || false, // required
 * //     breakingItems: "<OntologyBreakingItemList>", // required
 * //     summary: {
 * //       addedTriples: Number("int"), // required
 * //       removedTriples: Number("int"), // required
 * //       addedClasses: "<OntologyStringList>", // required
 * //       removedClasses: "<OntologyStringList>", // required
 * //       addedProperties: "<OntologyStringList>", // required
 * //       removedProperties: "<OntologyStringList>", // required
 * //       domainChanges: "<OntologyDomainChangeList>", // required
 * //       rangeChanges: "<OntologyDomainChangeList>", // required
 * //       removedClassInstances: [ // required
 * //         {
 * //           class: "STRING_VALUE", // required
 * //           instances: Number("int"), // required
 * //         },
 * //       ],
 * //     },
 * //     markdown: "STRING_VALUE",
 * //   },
 * //   impact: {
 * //     addedTriples: Number("int"),
 * //     removedTriples: Number("int"),
 * //     addedClasses: Number("int"),
 * //     removedClasses: Number("int"),
 * //     addedProperties: Number("int"),
 * //     removedProperties: Number("int"),
 * //     domainChanges: Number("int"),
 * //     rangeChanges: Number("int"),
 * //     removedClassInstances: Number("int"),
 * //     breakingItems: Number("int"),
 * //     analysis: {
 * //       from: "STRING_VALUE",
 * //       to: "STRING_VALUE", // required
 * //       changeSet: {
 * //         counts: {
 * //           addedTriples: Number("int"), // required
 * //           removedTriples: Number("int"), // required
 * //           addedClasses: Number("int"), // required
 * //           removedClasses: Number("int"), // required
 * //           addedProperties: Number("int"), // required
 * //           removedProperties: Number("int"), // required
 * //           domainChanges: Number("int"), // required
 * //           rangeChanges: Number("int"), // required
 * //         },
 * //         addedClasses: "<OntologyStringList>", // required
 * //         removedClasses: "<OntologyStringList>", // required
 * //         addedProperties: "<OntologyStringList>", // required
 * //         removedProperties: "<OntologyStringList>", // required
 * //         domainChanges: "<OntologyDomainChangeList>", // required
 * //         rangeChanges: "<OntologyDomainChangeList>", // required
 * //         breaking: true || false, // required
 * //         breakingItems: "<OntologyBreakingItemList>", // required
 * //       },
 * //       affected: {
 * //         classes: [ // required
 * //           {
 * //             iri: "STRING_VALUE", // required
 * //             label: "STRING_VALUE", // required
 * //             change: "added" || "removed" || "modified", // required
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //           },
 * //         ],
 * //         properties: [ // required
 * //           {
 * //             iri: "STRING_VALUE", // required
 * //             label: "STRING_VALUE", // required
 * //             change: "added" || "removed" || "modified", // required
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //             domainChanges: "<OntologyDomainChangeList>", // required
 * //             rangeChanges: "<OntologyDomainChangeList>", // required
 * //           },
 * //         ],
 * //         instances: {
 * //           total: Number("int"),
 * //           byClass: [ // required
 * //             {
 * //               iri: "STRING_VALUE", // required
 * //               label: "STRING_VALUE", // required
 * //               instances: Number("int"),
 * //             },
 * //           ],
 * //           source: "STRING_VALUE",
 * //           note: "STRING_VALUE",
 * //           affectedInstances: Number("int"),
 * //           graphs: "<OntologyStringList>",
 * //         },
 * //       },
 * //       aggregations: {
 * //         byClass: [ // required
 * //           {
 * //             iri: "STRING_VALUE", // required
 * //             label: "STRING_VALUE", // required
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //           },
 * //         ],
 * //         byProperty: [ // required
 * //           {
 * //             iri: "STRING_VALUE", // required
 * //             label: "STRING_VALUE", // required
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //           },
 * //         ],
 * //         unclassified: {
 * //           addedTriples: Number("int"), // required
 * //           removedTriples: Number("int"), // required
 * //         },
 * //         empty: true || false, // required
 * //         emptyReason: "STRING_VALUE",
 * //         method: "STRING_VALUE",
 * //         rowLimit: Number("int"),
 * //       },
 * //       dependencies: {
 * //         metrics: [ // required
 * //           {
 * //             metricId: "STRING_VALUE", // required
 * //             name: "STRING_VALUE",
 * //             matchedBy: "<OntologyStringList>", // required
 * //             source: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //         rules: [ // required
 * //           {
 * //             metricId: "STRING_VALUE", // required
 * //             ruleId: "STRING_VALUE",
 * //             level: "STRING_VALUE",
 * //             matchedBy: "STRING_VALUE", // required
 * //             source: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //         terms: [ // required
 * //           {
 * //             surface: "STRING_VALUE",
 * //             canonical: "STRING_VALUE",
 * //             lang: "STRING_VALUE",
 * //             source: "STRING_VALUE",
 * //             canonicalLabel: "STRING_VALUE",
 * //           },
 * //         ],
 * //         notes: [ // required
 * //           {
 * //             source: "STRING_VALUE", // required
 * //             error: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //         empty: true || false, // required
 * //         emptyReason: "STRING_VALUE",
 * //         method: "STRING_VALUE",
 * //       },
 * //       verification: {
 * //         sampled: [ // required
 * //           {
 * //             iri: "STRING_VALUE", // required
 * //             listed: Number("int"), // required
 * //             recounted: Number("int"), // required
 * //             consistent: true || false, // required
 * //           },
 * //         ],
 * //         consistent: true || false,
 * //         reason: "STRING_VALUE",
 * //         source: "STRING_VALUE",
 * //       },
 * //       inputs: {
 * //         from: {
 * //           versionId: "STRING_VALUE",
 * //           semver: "STRING_VALUE",
 * //           contentHash: "STRING_VALUE",
 * //           tripleCount: Number("int"),
 * //         },
 * //         to: {
 * //           versionId: "STRING_VALUE",
 * //           semver: "STRING_VALUE",
 * //           contentHash: "STRING_VALUE",
 * //           tripleCount: Number("int"),
 * //         },
 * //       },
 * //       inputsFingerprint: "STRING_VALUE",
 * //       empty: true || false, // required
 * //       emptyReason: "STRING_VALUE",
 * //       computedAt: "STRING_VALUE", // required
 * //       source: "STRING_VALUE", // required
 * //       readOnly: true || false, // required
 * //     },
 * //     analysisError: {
 * //       code: "STRING_VALUE", // required
 * //       message: "STRING_VALUE", // required
 * //       details: "DOCUMENT_VALUE",
 * //     },
 * //   },
 * //   current: { // OntologyPointer
 * //     name: "STRING_VALUE",
 * //     versionId: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE",
 * //     contentHash: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     updatedAt: "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param GetOntologyVersionProposalCommandInput - {@link GetOntologyVersionProposalCommandInput}
 * @returns {@link GetOntologyVersionProposalCommandOutput}
 * @see {@link GetOntologyVersionProposalCommandInput} for command's `input` shape.
 * @see {@link GetOntologyVersionProposalCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link InternalServerError} (server fault)
 *  Returned with HTTP 500 when the service fails unexpectedly. The message is a
 * fixed, generic description; the underlying cause is logged, never returned.
 *
 * @throws {@link ServiceUnavailableError} (server fault)
 *  Returned with HTTP 503 when the service, or a required dependency (including
 * one it needs to handle the request safely), is temporarily unavailable. For
 * example, a create that
 * carries a `clientToken` fails closed with this error when the retry-safety
 * store cannot be reached, rather than risk running the create twice. Retry
 * the request (with the same `clientToken`) after a backoff.
 *
 * @throws {@link ControlPlaneServiceServiceException}
 * <p>Base exception class for all service exceptions from ControlPlaneService service.</p>
 *
 *
 * @example Read one proposal
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   proposalId: "prop-1a2b3c4d5e6f"
 * };
 * const command = new GetOntologyVersionProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   diff: {
 *     breaking: false,
 *     breakingItems:     [],
 *     from: "ont-1a2b3c4d5e6f",
 *     summary: {
 *       addedClasses:       [],
 *       addedProperties:       [],
 *       addedTriples: 12,
 *       domainChanges:       [],
 *       rangeChanges:       [],
 *       removedClassInstances:       [],
 *       removedClasses:       [],
 *       removedProperties:       [],
 *       removedTriples: 0
 *     },
 *     to: "ont-draft-9f8e7d6c5b4a"
 *   },
 *   impact: {
 *     addedClasses: 1,
 *     addedProperties: 0,
 *     addedTriples: 12,
 *     analysis: {
 *       affected: {
 *         classes: [
 *           {
 *             addedTriples: 12,
 *             change: "added",
 *             iri: "urn:coa:class:Invoice",
 *             label: "Invoice",
 *             removedTriples: 0
 *           }
 *         ],
 *         instances: {
 *           byClass: [
 *             {
 *               iri: "urn:coa:class:Invoice",
 *               label: "Invoice"
 *             }
 *           ],
 *           note: "没有 A-Box 图，实例数不可算；未以 0 代替",
 *           source: "A-Box 未配置"
 *         },
 *         properties:         []
 *       },
 *       aggregations: {
 *         byClass: [
 *           {
 *             addedTriples: 12,
 *             iri: "urn:coa:class:Invoice",
 *             label: "Invoice",
 *             removedTriples: 0
 *           }
 *         ],
 *         byProperty:         [],
 *         empty: false,
 *         method: "SPARQL GROUP BY ?s ?p over (to MINUS from)",
 *         unclassified: {
 *           addedTriples: 0,
 *           removedTriples: 0
 *         }
 *       },
 *       changeSet: {
 *         addedClasses: [
 *           "urn:coa:class:Invoice"
 *         ],
 *         addedProperties:         [],
 *         breaking: false,
 *         breakingItems:         [],
 *         counts: {
 *           addedClasses: 1,
 *           addedProperties: 0,
 *           addedTriples: 12,
 *           domainChanges: 0,
 *           rangeChanges: 0,
 *           removedClasses: 0,
 *           removedProperties: 0,
 *           removedTriples: 0
 *         },
 *         domainChanges:         [],
 *         rangeChanges:         [],
 *         removedClasses:         [],
 *         removedProperties:         []
 *       },
 *       computedAt: "2026-10-02T09:31:00Z",
 *       dependencies: {
 *         empty: true,
 *         emptyReason: "无指标或规则依赖命中",
 *         metrics:         [],
 *         notes:         [],
 *         rules:         [],
 *         terms:         []
 *       },
 *       empty: false,
 *       from: "ont-1a2b3c4d5e6f",
 *       readOnly: true,
 *       source: "diff + A-Box + 指标注册表（只读）",
 *       to: "ont-draft-9f8e7d6c5b4a",
 *       verification: {
 *         reason: "无受影响的类可抽样",
 *         sampled:         []
 *       }
 *     },
 *     breakingItems: 0,
 *     domainChanges: 0,
 *     rangeChanges: 0,
 *     removedClassInstances: 0,
 *     removedClasses: 0,
 *     removedProperties: 0,
 *     removedTriples: 0
 *   },
 *   proposal: {
 *     againstVersion: "ont-1a2b3c4d5e6f",
 *     breaking: false,
 *     changeSummary: "add Invoice class",
 *     proposalId: "prop-1a2b3c4d5e6f",
 *     status: "proposed",
 *     versionId: "ont-draft-9f8e7d6c5b4a"
 *   },
 *   version: {
 *     id: "ont-draft-9f8e7d6c5b4a",
 *     semver: "1.1.0",
 *     status: "proposed"
 *   },
 *   versionStatus: "proposed"
 * }
 * *\/
 * ```
 *
 * @example Read one proposal whose impact analysis failed
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   proposalId: "prop-6f5e4d3c2b1a"
 * };
 * const command = new GetOntologyVersionProposalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   diff: {
 *     breaking: false,
 *     breakingItems:     [],
 *     summary: {
 *       addedClasses:       [],
 *       addedProperties:       [],
 *       addedTriples: 0,
 *       domainChanges:       [],
 *       rangeChanges:       [],
 *       removedClassInstances:       [],
 *       removedClasses:       [],
 *       removedProperties:       [],
 *       removedTriples: 0
 *     },
 *     to: "ont-draft-1029384756ab"
 *   },
 *   impact: {
 *     addedTriples: 0,
 *     analysisError: {
 *       code: "E_IMPACT_PREVIOUS_VERSION_UNREADABLE",
 *       details: {
 *         versionId: "ont-1a2b3c4d5e6f"
 *       },
 *       message: "baseline version ont-1a2b3c4d5e6f could not be read"
 *     },
 *     removedTriples: 0
 *   },
 *   proposal: {
 *     breaking: false,
 *     proposalId: "prop-6f5e4d3c2b1a",
 *     status: "proposed",
 *     versionId: "ont-draft-1029384756ab"
 *   },
 *   version: {
 *     id: "ont-draft-1029384756ab",
 *     semver: "1.1.0",
 *     status: "proposed"
 *   },
 *   versionStatus: "proposed"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologyVersionProposalCommand extends $Command
  .classBuilder<
    GetOntologyVersionProposalCommandInput,
    GetOntologyVersionProposalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntologyVersionProposal", {})
  .n("ControlPlaneServiceClient", "GetOntologyVersionProposalCommand")
  .sc(GetOntologyVersionProposal$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologyVersionProposalInput;
      output: OntologyProposalDetail;
    };
    sdk: {
      input: GetOntologyVersionProposalCommandInput;
      output: GetOntologyVersionProposalCommandOutput;
    };
  };
}
