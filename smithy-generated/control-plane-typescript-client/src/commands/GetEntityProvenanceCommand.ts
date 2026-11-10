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
import type { EntityProvenanceReport, GetEntityProvenanceInput } from "../models/models_0";
import { GetEntityProvenance$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetEntityProvenanceCommand}.
 */
export interface GetEntityProvenanceCommandInput extends GetEntityProvenanceInput {}
/**
 * @public
 *
 * The output of {@link GetEntityProvenanceCommand}.
 */
export interface GetEntityProvenanceCommandOutput extends EntityProvenanceReport, __MetadataBearer {}

/**
 * Read the per-field provenance report for one A-Box entity.
 *
 * Every field carries an explicit three-state badge (`evidenced`, `inferred`,
 * `none`); a field without evidence is shown as `none`, never omitted.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetEntityProvenanceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetEntityProvenanceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetEntityProvenanceInput
 *   entityId: "STRING_VALUE", // required
 *   limit: Number("int"),
 * };
 * const command = new GetEntityProvenanceCommand(input);
 * const response = await client.send(command);
 * // { // EntityProvenanceReport
 * //   iri: "STRING_VALUE", // required
 * //   label: "STRING_VALUE", // required
 * //   fields: [ // ProvenanceFieldList // required
 * //     { // ProvenanceField
 * //       property: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       values: [ // EntityTermList // required
 * //         { // EntityTerm
 * //           kind: "STRING_VALUE", // required
 * //           value: "STRING_VALUE", // required
 * //           iri: "STRING_VALUE",
 * //           datatype: "STRING_VALUE",
 * //           lang: "STRING_VALUE",
 * //         },
 * //       ],
 * //       valueText: "STRING_VALUE",
 * //       asserted: true || false, // required
 * //       inferredOnly: true || false, // required
 * //       badge: { // EntityBadge
 * //         state: "STRING_VALUE", // required
 * //         label: "STRING_VALUE", // required
 * //         basis: "STRING_VALUE", // required
 * //         judge: "STRING_VALUE",
 * //       },
 * //       hasSourceRef: true || false, // required
 * //       hasProv: true || false, // required
 * //       links: [ // ProvenanceLinkList // required
 * //         { // ProvenanceLink
 * //           kind: "STRING_VALUE", // required
 * //           ref: "STRING_VALUE",
 * //           url: "STRING_VALUE",
 * //           documentId: "STRING_VALUE",
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   statements: [ // required
 * //     {
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
 * //       valueText: "STRING_VALUE",
 * //       asserted: true || false, // required
 * //       inferredOnly: true || false, // required
 * //       badge: {
 * //         state: "STRING_VALUE", // required
 * //         label: "STRING_VALUE", // required
 * //         basis: "STRING_VALUE", // required
 * //         judge: "STRING_VALUE",
 * //       },
 * //       hasSourceRef: true || false, // required
 * //       hasProv: true || false, // required
 * //       links: [ // required
 * //         {
 * //           kind: "STRING_VALUE", // required
 * //           ref: "STRING_VALUE",
 * //           url: "STRING_VALUE",
 * //           documentId: "STRING_VALUE",
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   activities: [ // ProvenanceActivityList // required
 * //     { // ProvenanceActivity
 * //       activityId: "STRING_VALUE", // required
 * //       relation: "STRING_VALUE", // required
 * //       object: "STRING_VALUE",
 * //       graph: "STRING_VALUE",
 * //     },
 * //   ],
 * //   citations: [ // ProvenanceCitationList // required
 * //     { // ProvenanceCitation
 * //       kind: "STRING_VALUE", // required
 * //       ref: "STRING_VALUE",
 * //       text: "STRING_VALUE",
 * //       documentId: "STRING_VALUE",
 * //       url: "STRING_VALUE",
 * //     },
 * //   ],
 * //   summary: { // ProvenanceSummary
 * //     total: Number("int"), // required
 * //     evidenced: Number("int"), // required
 * //     inferred: Number("int"), // required
 * //     none: Number("int"), // required
 * //     withSourceRef: Number("int"), // required
 * //     withProv: Number("int"), // required
 * //     coverageRate: Number("double"), // required
 * //   },
 * //   evidenceBadge: {
 * //     state: "STRING_VALUE", // required
 * //     label: "STRING_VALUE", // required
 * //     basis: "STRING_VALUE", // required
 * //     judge: "STRING_VALUE",
 * //   },
 * //   namedGraphs: [ // StringList // required
 * //     "STRING_VALUE",
 * //   ],
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
 * //   empty: true || false, // required
 * //   emptyReason: "STRING_VALUE",
 * //   note: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param GetEntityProvenanceCommandInput - {@link GetEntityProvenanceCommandInput}
 * @returns {@link GetEntityProvenanceCommandOutput}
 * @see {@link GetEntityProvenanceCommandInput} for command's `input` shape.
 * @see {@link GetEntityProvenanceCommandOutput} for command's `response` shape.
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
 * @example Read entity provenance
 * ```javascript
 * //
 * const input = {
 *   entityId: "urn:coa:entity:contract-ledger",
 *   limit: 50
 * };
 * const command = new GetEntityProvenanceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   activities:   [],
 *   citations: [
 *     {
 *       kind: "doc",
 *       ref: "doc-1",
 *       text: "Contract Ledger belongs to Archive",
 *       url: "/source/resolve?ref=doc-1"
 *     }
 *   ],
 *   empty: false,
 *   evidenceBadge: {
 *     basis: "字段值命中 PROV/sourceRef 证据文本",
 *     label: "有溯源",
 *     state: "evidenced"
 *   },
 *   fields: [
 *     {
 *       asserted: true,
 *       badge: {
 *         basis: "事实账本 fact-1a2b3c4d5e6f",
 *         label: "有溯源",
 *         state: "evidenced"
 *       },
 *       hasProv: true,
 *       hasSourceRef: true,
 *       inferredOnly: false,
 *       label: "belongs to",
 *       links: [
 *         {
 *           kind: "fact",
 *           ref: "fact-1a2b3c4d5e6f",
 *           url: "/facts/fact-1a2b3c4d5e6f/events"
 *         }
 *       ],
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
 *   iri: "urn:coa:entity:contract-ledger",
 *   label: "Contract Ledger",
 *   namedGraphs: [
 *     "urn:coa:graph:asserted"
 *   ],
 *   note: "每个字段都有徽标；无溯源显式显示「无」",
 *   provenance: {
 *     count: 1,
 *     items:     [],
 *     unavailable: false
 *   },
 *   statements:   [],
 *   summary: {
 *     coverageRate: 1.0,
 *     evidenced: 1,
 *     inferred: 0,
 *     none: 0,
 *     total: 1,
 *     withProv: 1,
 *     withSourceRef: 1
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetEntityProvenanceCommand extends $Command
  .classBuilder<
    GetEntityProvenanceCommandInput,
    GetEntityProvenanceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetEntityProvenance", {})
  .n("ControlPlaneServiceClient", "GetEntityProvenanceCommand")
  .sc(GetEntityProvenance$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetEntityProvenanceInput;
      output: EntityProvenanceReport;
    };
    sdk: {
      input: GetEntityProvenanceCommandInput;
      output: GetEntityProvenanceCommandOutput;
    };
  };
}
