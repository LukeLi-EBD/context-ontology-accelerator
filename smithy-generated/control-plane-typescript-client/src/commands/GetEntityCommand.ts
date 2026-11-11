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
import type { EntityDetail, GetEntityInput } from "../models/models_0";
import { GetEntity$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetEntityCommand}.
 */
export interface GetEntityCommandInput extends GetEntityInput {}
/**
 * @public
 *
 * The output of {@link GetEntityCommand}.
 */
export interface GetEntityCommandOutput extends EntityDetail, __MetadataBearer {}

/**
 * Read one A-Box entity by IRI.
 *
 * The IRI is percent-encoded in the path so its slashes are not parsed as path
 * separators. `limit` caps the neighbourhood, not the property list.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetEntityCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetEntityCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetEntityInput
 *   entityId: "STRING_VALUE", // required
 *   limit: Number("int"),
 * };
 * const command = new GetEntityCommand(input);
 * const response = await client.send(command);
 * // { // EntityDetail
 * //   iri: "STRING_VALUE", // required
 * //   label: "STRING_VALUE", // required
 * //   classes: [ // EntityClassList // required
 * //     { // EntityClass
 * //       iri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       labeled: true || false, // required
 * //       inferredOnly: true || false, // required
 * //       instanceCount: Number("int"), // required
 * //       chain: [ // EntityClassLinkList // required
 * //         { // EntityClassLink
 * //           iri: "STRING_VALUE", // required
 * //           label: "STRING_VALUE", // required
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   requiredProperties: [ // EntityRequiredList // required
 * //     { // EntityRequired
 * //       property: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       minCount: Number("int"), // required
 * //       declaredOn: [ // StringList // required
 * //         "STRING_VALUE",
 * //       ],
 * //       values: [ // EntityTermList // required
 * //         { // EntityTerm
 * //           kind: "STRING_VALUE", // required
 * //           value: "STRING_VALUE", // required
 * //           iri: "STRING_VALUE",
 * //           datatype: "STRING_VALUE",
 * //           lang: "STRING_VALUE",
 * //         },
 * //       ],
 * //       valueCount: Number("int"), // required
 * //       satisfied: true || false, // required
 * //     },
 * //   ],
 * //   requiredStatus: "STRING_VALUE", // required
 * //   properties: [ // EntityPropertyList // required
 * //     { // EntityProperty
 * //       property: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       values: [ // required
 * //         {
 * //           kind: "STRING_VALUE", // required
 * //           value: "STRING_VALUE", // required
 * //           iri: "STRING_VALUE",
 * //           datatype: "STRING_VALUE",
 * //           lang: "STRING_VALUE",
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   neighbors: { // EntityNeighbors
 * //     nodes: [ // EntityNodeList // required
 * //       { // EntityNode
 * //         iri: "STRING_VALUE", // required
 * //         label: "STRING_VALUE", // required
 * //         inferred: true || false, // required
 * //       },
 * //     ],
 * //     edges: [ // EntityEdgeList // required
 * //       { // EntityEdge
 * //         s: "STRING_VALUE", // required
 * //         p: "STRING_VALUE", // required
 * //         o: "STRING_VALUE", // required
 * //         graph: "STRING_VALUE", // required
 * //         inferred: true || false, // required
 * //       },
 * //     ],
 * //     truncated: true || false, // required
 * //   },
 * //   instanceCount: Number("int"), // required
 * //   relatedMetrics: { // EntityRelatedMetrics
 * //     status: "STRING_VALUE", // required
 * //     reason: "STRING_VALUE",
 * //     items: [ // RelatedMetricList // required
 * //       { // RelatedMetric
 * //         metricId: "STRING_VALUE", // required
 * //         nameZh: "STRING_VALUE",
 * //         domain: "STRING_VALUE",
 * //         grain: "STRING_VALUE",
 * //         publishable: true || false,
 * //         bindings: [ // RelatedMetricBindingList // required
 * //           { // RelatedMetricBinding
 * //             role: "STRING_VALUE",
 * //             factTable: "STRING_VALUE",
 * //             entityColumn: "STRING_VALUE",
 * //           },
 * //         ],
 * //         matchBasis: [ // required
 * //           "STRING_VALUE",
 * //         ],
 * //       },
 * //     ],
 * //     matchBasis: "<StringList>", // required
 * //   },
 * //   sources: [ // EntitySourceList // required
 * //     { // EntitySource
 * //       kind: "STRING_VALUE", // required
 * //       ref: "STRING_VALUE", // required
 * //       text: "STRING_VALUE",
 * //       resolveUrl: "STRING_VALUE", // required
 * //       href: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   evidenceBadge: { // EntityBadge
 * //     state: "STRING_VALUE", // required
 * //     label: "STRING_VALUE", // required
 * //     basis: "STRING_VALUE", // required
 * //     judge: "STRING_VALUE",
 * //   },
 * //   tbox: { // EntityTbox
 * //     versionId: "STRING_VALUE",
 * //     semver: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //   },
 * //   sampledAt: "STRING_VALUE", // required
 * //   namedGraphs: "<StringList>", // required
 * //   provenance: { // EntityProvenance
 * //     count: Number("int"), // required
 * //     items: [ // EntityProvenanceItemList // required
 * //       { // EntityProvenanceItem
 * //         factId: "STRING_VALUE", // required
 * //         predicate: "STRING_VALUE", // required
 * //         object: {
 * //           kind: "STRING_VALUE", // required
 * //           value: "STRING_VALUE", // required
 * //           iri: "STRING_VALUE",
 * //           datatype: "STRING_VALUE",
 * //           lang: "STRING_VALUE",
 * //         },
 * //         state: "STRING_VALUE", // required
 * //         sourceKind: "STRING_VALUE",
 * //         documentId: "STRING_VALUE",
 * //         candidateId: "STRING_VALUE",
 * //         assertedAt: "STRING_VALUE", // required
 * //         conflict: true || false, // required
 * //       },
 * //     ],
 * //     unavailable: true || false,
 * //   },
 * // };
 *
 * ```
 *
 * @param GetEntityCommandInput - {@link GetEntityCommandInput}
 * @returns {@link GetEntityCommandOutput}
 * @see {@link GetEntityCommandInput} for command's `input` shape.
 * @see {@link GetEntityCommandOutput} for command's `response` shape.
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
 * @example Read one entity
 * ```javascript
 * //
 * const input = {
 *   entityId: "urn:coa:entity:contract-ledger",
 *   limit: 50
 * };
 * const command = new GetEntityCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   classes: [
 *     {
 *       chain: [
 *         {
 *           iri: "urn:coa:class:Thing",
 *           label: "Thing"
 *         }
 *       ],
 *       inferredOnly: false,
 *       instanceCount: 12,
 *       iri: "urn:coa:class:BusinessEntity",
 *       label: "Business Entity",
 *       labeled: true
 *     }
 *   ],
 *   evidenceBadge: {
 *     basis: "仅推理图出现，无断言 sourceRef / PROV",
 *     label: "仅推理",
 *     state: "inferred"
 *   },
 *   instanceCount: 12,
 *   iri: "urn:coa:entity:contract-ledger",
 *   label: "Contract Ledger",
 *   namedGraphs: [
 *     "urn:coa:graph:asserted"
 *   ],
 *   neighbors: {
 *     edges:     [],
 *     nodes:     [],
 *     truncated: false
 *   },
 *   properties: [
 *     {
 *       label: "belongs to",
 *       property: "urn:coa:predicate:belongs-to",
 *       values: [
 *         {
 *           iri: "urn:coa:entity:archive",
 *           kind: "iri",
 *           value: "urn:coa:entity:archive"
 *         }
 *       ]
 *     }
 *   ],
 *   provenance: {
 *     count: 1,
 *     items:     [],
 *     unavailable: false
 *   },
 *   relatedMetrics: {
 *     items:     [],
 *     matchBasis:     [],
 *     reason: "no metric binding",
 *     status: "empty"
 *   },
 *   requiredProperties:   [],
 *   requiredStatus: "satisfied",
 *   sampledAt: "2026-10-02T09:00:00Z",
 *   sources:   [],
 *   tbox: {
 *     graph: "urn:coa:graph:tbox",
 *     semver: "1.4.0",
 *     versionId: "8c7d6e5f-4a3b-4c2d-8e1f-0a9b8c7d6e5f"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetEntityCommand extends $Command
  .classBuilder<
    GetEntityCommandInput,
    GetEntityCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetEntity", {})
  .n("ControlPlaneServiceClient", "GetEntityCommand")
  .sc(GetEntity$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetEntityInput;
      output: EntityDetail;
    };
    sdk: {
      input: GetEntityCommandInput;
      output: GetEntityCommandOutput;
    };
  };
}
