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
import type { FactConflictList, ListFactConflictsInput } from "../models/models_0";
import { ListFactConflicts$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListFactConflictsCommand}.
 */
export interface ListFactConflictsCommandInput extends ListFactConflictsInput {}
/**
 * @public
 *
 * The output of {@link ListFactConflictsCommand}.
 */
export interface ListFactConflictsCommandOutput extends FactConflictList, __MetadataBearer {}

/**
 * List (subject, predicate) groups that hold more than one active value.
 *
 * Accepted conflicts are omitted unless `includeAccepted` is true. Each group
 * carries its full adjudication history so the console can render undo.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListFactConflictsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListFactConflictsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListFactConflictsInput
 *   namespaceId: "STRING_VALUE", // required
 *   includeAccepted: true || false,
 * };
 * const command = new ListFactConflictsCommand(input);
 * const response = await client.send(command);
 * // { // FactConflictList
 * //   conflicts: [ // FactConflictItemList // required
 * //     { // FactConflict
 * //       subject: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       values: [ // FactIriList // required
 * //         "STRING_VALUE",
 * //       ],
 * //       accepted: true || false, // required
 * //       pending: true || false, // required
 * //       facts: [ // FactConflictFactList // required
 * //         { // FactConflictFact
 * //           factId: "STRING_VALUE", // required
 * //           object: "STRING_VALUE", // required
 * //           objectKind: "STRING_VALUE", // required
 * //           source: { // FactSource
 * //             kind: "STRING_VALUE",
 * //             documentId: "STRING_VALUE",
 * //             runId: "STRING_VALUE",
 * //             candidateId: "STRING_VALUE",
 * //           },
 * //           assertedAt: "STRING_VALUE",
 * //           evidence: { // FactConflictEvidence
 * //             chunkId: "STRING_VALUE",
 * //             text: "STRING_VALUE",
 * //           },
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   count: Number("int"), // required
 * //   pending: Number("int"), // required
 * //   includeAccepted: true || false,
 * //   adjudications: [ // FactAdjudicationList
 * //     { // FactAdjudication
 * //       subject: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       eventId: Number("int"),
 * //       action: "STRING_VALUE",
 * //       actor: "STRING_VALUE",
 * //       reason: "STRING_VALUE",
 * //       at: "STRING_VALUE", // required
 * //       status: "STRING_VALUE", // required
 * //       kept: "STRING_VALUE",
 * //       values: [ // required
 * //         "STRING_VALUE",
 * //       ],
 * //       object: "STRING_VALUE",
 * //       undoneBy: { // FactUndoReference
 * //         eventId: Number("int"), // required
 * //         actor: "STRING_VALUE",
 * //         reason: "STRING_VALUE",
 * //         at: "STRING_VALUE", // required
 * //       },
 * //       history: [ // FactAdjudicationEventList // required
 * //         { // FactAdjudicationEvent
 * //           eventId: Number("int"), // required
 * //           action: "STRING_VALUE", // required
 * //           actor: "STRING_VALUE",
 * //           reason: "STRING_VALUE",
 * //           at: "STRING_VALUE", // required
 * //           payload: "DOCUMENT_VALUE",
 * //         },
 * //       ],
 * //       effective: { // FactAdjudicationEffective
 * //         activeCount: Number("int"), // required
 * //         values: [ // required
 * //           "STRING_VALUE",
 * //         ],
 * //         conflict: true || false, // required
 * //         acceptedConflict: true || false, // required
 * //       },
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListFactConflictsCommandInput - {@link ListFactConflictsCommandInput}
 * @returns {@link ListFactConflictsCommandOutput}
 * @see {@link ListFactConflictsCommandInput} for command's `input` shape.
 * @see {@link ListFactConflictsCommandOutput} for command's `response` shape.
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
 * @example List pending conflicts
 * ```javascript
 * //
 * const input = {
 *   includeAccepted: false,
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new ListFactConflictsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   adjudications: [
 *     {
 *       at: "2026-10-01T08:00:00Z",
 *       effective: {
 *         acceptedConflict: false,
 *         activeCount: 2,
 *         conflict: true,
 *         values: [
 *           "urn:coa:entity:archive",
 *           "urn:coa:entity:legal"
 *         ]
 *       },
 *       history:       [],
 *       predicate: "urn:coa:predicate:belongs-to",
 *       status: "in_effect",
 *       subject: "urn:coa:entity:contract-ledger",
 *       values: [
 *         "urn:coa:entity:archive",
 *         "urn:coa:entity:legal"
 *       ]
 *     }
 *   ],
 *   conflicts: [
 *     {
 *       accepted: false,
 *       facts: [
 *         {
 *           factId: "fact-1a2b3c4d5e6f",
 *           object: "urn:coa:entity:archive",
 *           objectKind: "iri"
 *         },
 *         {
 *           factId: "fact-0f1e2d3c4b5a",
 *           object: "urn:coa:entity:legal",
 *           objectKind: "iri"
 *         }
 *       ],
 *       pending: true,
 *       predicate: "urn:coa:predicate:belongs-to",
 *       subject: "urn:coa:entity:contract-ledger",
 *       values: [
 *         "urn:coa:entity:archive",
 *         "urn:coa:entity:legal"
 *       ]
 *     }
 *   ],
 *   count: 1,
 *   includeAccepted: false,
 *   pending: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListFactConflictsCommand extends $Command
  .classBuilder<
    ListFactConflictsCommandInput,
    ListFactConflictsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListFactConflicts", {})
  .n("ControlPlaneServiceClient", "ListFactConflictsCommand")
  .sc(ListFactConflicts$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListFactConflictsInput;
      output: FactConflictList;
    };
    sdk: {
      input: ListFactConflictsCommandInput;
      output: ListFactConflictsCommandOutput;
    };
  };
}
