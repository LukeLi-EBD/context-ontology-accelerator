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
import type { OntologyProposal, ProposeOntologyVersionInput } from "../models/models_1";
import { ProposeOntologyVersion$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ProposeOntologyVersionCommand}.
 */
export interface ProposeOntologyVersionCommandInput extends ProposeOntologyVersionInput {}
/**
 * @public
 *
 * The output of {@link ProposeOntologyVersionCommand}.
 */
export interface ProposeOntologyVersionCommandOutput extends OntologyProposal, __MetadataBearer {}

/**
 * File a proposal for a registered draft version.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ProposeOntologyVersionCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ProposeOntologyVersionCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ProposeOntologyVersionInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   versionId: "STRING_VALUE", // required
 *   rationale: "STRING_VALUE", // required
 *   againstVersion: "STRING_VALUE",
 *   actor: "STRING_VALUE",
 * };
 * const command = new ProposeOntologyVersionCommand(input);
 * const response = await client.send(command);
 * // { // OntologyProposal
 * //   proposalId: "STRING_VALUE", // required
 * //   versionId: "STRING_VALUE", // required
 * //   againstVersion: "STRING_VALUE",
 * //   changeSummary: "STRING_VALUE",
 * //   status: "proposed" || "review" || "approved" || "published" || "rejected", // required
 * //   breaking: true || false, // required
 * //   acknowledgedBreaking: true || false,
 * //   diff: { // OntologyDiff
 * //     from: "STRING_VALUE",
 * //     to: "STRING_VALUE", // required
 * //     breaking: true || false, // required
 * //     breakingItems: [ // OntologyBreakingItemList // required
 * //       { // OntologyBreakingItem
 * //         kind: "STRING_VALUE", // required
 * //         iri: "STRING_VALUE",
 * //         property: "STRING_VALUE",
 * //         from: [ // OntologyStringList
 * //           "STRING_VALUE",
 * //         ],
 * //         to: [
 * //           "STRING_VALUE",
 * //         ],
 * //       },
 * //     ],
 * //     summary: { // OntologyDiffSummary
 * //       addedTriples: Number("int"), // required
 * //       removedTriples: Number("int"), // required
 * //       addedClasses: [ // required
 * //         "STRING_VALUE",
 * //       ],
 * //       removedClasses: [ // required
 * //         "STRING_VALUE",
 * //       ],
 * //       addedProperties: [ // required
 * //         "STRING_VALUE",
 * //       ],
 * //       removedProperties: "<OntologyStringList>", // required
 * //       domainChanges: [ // OntologyDomainChangeList // required
 * //         { // OntologyDomainChange
 * //           property: "STRING_VALUE", // required
 * //           from: "<OntologyStringList>", // required
 * //           to: "<OntologyStringList>", // required
 * //         },
 * //       ],
 * //       rangeChanges: [ // required
 * //         {
 * //           property: "STRING_VALUE", // required
 * //           from: "<OntologyStringList>", // required
 * //           to: "<OntologyStringList>", // required
 * //         },
 * //       ],
 * //       removedClassInstances: [ // OntologyClassInstanceList // required
 * //         { // OntologyClassInstance
 * //           class: "STRING_VALUE", // required
 * //           instances: Number("int"), // required
 * //         },
 * //       ],
 * //     },
 * //     markdown: "STRING_VALUE",
 * //   },
 * //   impact: { // OntologyImpact
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
 * //     analysis: { // OntologyImpactAnalysis
 * //       from: "STRING_VALUE",
 * //       to: "STRING_VALUE", // required
 * //       changeSet: { // OntologyImpactChangeSet
 * //         counts: { // OntologyImpactCounts
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
 * //         domainChanges: [ // required
 * //           {
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
 * //         breaking: true || false, // required
 * //         breakingItems: [ // required
 * //           {
 * //             kind: "STRING_VALUE", // required
 * //             iri: "STRING_VALUE",
 * //             property: "STRING_VALUE",
 * //             from: "<OntologyStringList>",
 * //             to: "<OntologyStringList>",
 * //           },
 * //         ],
 * //       },
 * //       affected: { // OntologyImpactAffected
 * //         classes: [ // OntologyImpactClassList // required
 * //           { // OntologyImpactClass
 * //             iri: "STRING_VALUE", // required
 * //             label: "STRING_VALUE", // required
 * //             change: "added" || "removed" || "modified", // required
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //           },
 * //         ],
 * //         properties: [ // OntologyImpactPropertyList // required
 * //           { // OntologyImpactProperty
 * //             iri: "STRING_VALUE", // required
 * //             label: "STRING_VALUE", // required
 * //             change: "added" || "removed" || "modified", // required
 * //             addedTriples: Number("int"), // required
 * //             removedTriples: Number("int"), // required
 * //             domainChanges: "<OntologyDomainChangeList>", // required
 * //             rangeChanges: "<OntologyDomainChangeList>", // required
 * //           },
 * //         ],
 * //         instances: { // OntologyImpactInstances
 * //           total: Number("int"),
 * //           byClass: [ // OntologyImpactClassInstanceList // required
 * //             { // OntologyImpactClassInstances
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
 * //       aggregations: { // OntologyImpactAggregations
 * //         byClass: [ // OntologyImpactAggregationList // required
 * //           { // OntologyImpactAggregation
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
 * //         unclassified: { // OntologyImpactTripleCount
 * //           addedTriples: Number("int"), // required
 * //           removedTriples: Number("int"), // required
 * //         },
 * //         empty: true || false, // required
 * //         emptyReason: "STRING_VALUE",
 * //         method: "STRING_VALUE",
 * //         rowLimit: Number("int"),
 * //       },
 * //       dependencies: { // OntologyImpactDependencies
 * //         metrics: [ // OntologyImpactMetricList // required
 * //           { // OntologyImpactMetric
 * //             metricId: "STRING_VALUE", // required
 * //             name: "STRING_VALUE",
 * //             matchedBy: "<OntologyStringList>", // required
 * //             source: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //         rules: [ // OntologyImpactRuleList // required
 * //           { // OntologyImpactRule
 * //             metricId: "STRING_VALUE", // required
 * //             ruleId: "STRING_VALUE",
 * //             level: "STRING_VALUE",
 * //             matchedBy: "STRING_VALUE", // required
 * //             source: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //         terms: [ // OntologyImpactTermList // required
 * //           { // OntologyImpactTerm
 * //             surface: "STRING_VALUE",
 * //             canonical: "STRING_VALUE",
 * //             lang: "STRING_VALUE",
 * //             source: "STRING_VALUE",
 * //             canonicalLabel: "STRING_VALUE",
 * //           },
 * //         ],
 * //         notes: [ // OntologyImpactNoteList // required
 * //           { // OntologyImpactNote
 * //             source: "STRING_VALUE", // required
 * //             error: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //         empty: true || false, // required
 * //         emptyReason: "STRING_VALUE",
 * //         method: "STRING_VALUE",
 * //       },
 * //       verification: { // OntologyImpactVerification
 * //         sampled: [ // OntologyImpactSampleList // required
 * //           { // OntologyImpactSample
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
 * //       inputs: { // OntologyImpactInputs
 * //         from: { // OntologyImpactVersionRef
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
 * //     analysisError: { // OntologyImpactError
 * //       code: "STRING_VALUE", // required
 * //       message: "STRING_VALUE", // required
 * //       details: "DOCUMENT_VALUE",
 * //     },
 * //   },
 * //   createdBy: "STRING_VALUE",
 * //   createdAt: "STRING_VALUE",
 * //   approvedBy: "STRING_VALUE",
 * //   approvedAt: "STRING_VALUE",
 * //   publishedAt: "STRING_VALUE",
 * //   versionStatus: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated",
 * // };
 *
 * ```
 *
 * @param ProposeOntologyVersionCommandInput - {@link ProposeOntologyVersionCommandInput}
 * @returns {@link ProposeOntologyVersionCommandOutput}
 * @see {@link ProposeOntologyVersionCommandInput} for command's `input` shape.
 * @see {@link ProposeOntologyVersionCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Propose a draft against the current version
 * ```javascript
 * //
 * const input = {
 *   actor: "operator",
 *   againstVersion: "ont-1a2b3c4d5e6f",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   rationale: "add Invoice class",
 *   versionId: "ont-draft-9f8e7d6c5b4a"
 * };
 * const command = new ProposeOntologyVersionCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   againstVersion: "ont-1a2b3c4d5e6f",
 *   breaking: false,
 *   changeSummary: "add Invoice class",
 *   proposalId: "prop-1a2b3c4d5e6f",
 *   status: "proposed",
 *   versionId: "ont-draft-9f8e7d6c5b4a"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ProposeOntologyVersionCommand extends $Command
  .classBuilder<
    ProposeOntologyVersionCommandInput,
    ProposeOntologyVersionCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ProposeOntologyVersion", {})
  .n("ControlPlaneServiceClient", "ProposeOntologyVersionCommand")
  .sc(ProposeOntologyVersion$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ProposeOntologyVersionInput;
      output: OntologyProposal;
    };
    sdk: {
      input: ProposeOntologyVersionCommandInput;
      output: ProposeOntologyVersionCommandOutput;
    };
  };
}
