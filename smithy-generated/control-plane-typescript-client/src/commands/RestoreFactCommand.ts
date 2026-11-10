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
import type { FactRecord, RestoreFactInput } from "../models/models_0";
import { RestoreFact$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RestoreFactCommand}.
 */
export interface RestoreFactCommandInput extends RestoreFactInput {}
/**
 * @public
 *
 * The output of {@link RestoreFactCommand}.
 */
export interface RestoreFactCommandOutput extends FactRecord, __MetadataBearer {}

/**
 * Restore a retracted assertion row.
 *
 * Restoring an active row is a no-op that returns its current state.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RestoreFactCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RestoreFactCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RestoreFactInput
 *   namespaceId: "STRING_VALUE", // required
 *   factId: "STRING_VALUE", // required
 *   actor: "STRING_VALUE",
 * };
 * const command = new RestoreFactCommand(input);
 * const response = await client.send(command);
 * // { // FactRecord
 * //   factId: "STRING_VALUE", // required
 * //   subject: "STRING_VALUE", // required
 * //   predicate: "STRING_VALUE", // required
 * //   object: { // FactObject
 * //     kind: "STRING_VALUE", // required
 * //     value: "STRING_VALUE", // required
 * //     iri: "STRING_VALUE",
 * //   },
 * //   graph: "STRING_VALUE", // required
 * //   state: "active" || "retracted" || "superseded", // required
 * //   source: { // FactSource
 * //     kind: "STRING_VALUE",
 * //     documentId: "STRING_VALUE",
 * //     runId: "STRING_VALUE",
 * //     candidateId: "STRING_VALUE",
 * //   },
 * //   assertedAt: "STRING_VALUE",
 * //   retractedAt: "STRING_VALUE",
 * //   retractReason: "STRING_VALUE",
 * //   acceptedConflict: true || false,
 * //   resolution: "STRING_VALUE",
 * //   resolvedBy: "STRING_VALUE",
 * //   resolvedAt: "STRING_VALUE",
 * //   supersededBy: "STRING_VALUE",
 * //   mergedFrom: [ // FactIdList
 * //     "STRING_VALUE",
 * //   ],
 * //   conflict: true || false,
 * //   duplicate: true || false,
 * //   events: [ // FactEventList
 * //     { // FactEvent
 * //       eventId: Number("int"), // required
 * //       factId: "STRING_VALUE", // required
 * //       action: "STRING_VALUE", // required
 * //       actor: "STRING_VALUE",
 * //       reason: "STRING_VALUE",
 * //       batchId: "STRING_VALUE",
 * //       payload: "DOCUMENT_VALUE",
 * //       prevEvent: Number("int"),
 * //       hash: "STRING_VALUE",
 * //       createdAt: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param RestoreFactCommandInput - {@link RestoreFactCommandInput}
 * @returns {@link RestoreFactCommandOutput}
 * @see {@link RestoreFactCommandInput} for command's `input` shape.
 * @see {@link RestoreFactCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Restore a retracted fact
 * ```javascript
 * //
 * const input = {
 *   actor: "operator",
 *   factId: "fact-1a2b3c4d5e6f",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   reason: "retracted in error"
 * };
 * const command = new RestoreFactCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   assertedAt: "2026-10-01T08:00:00Z",
 *   conflict: false,
 *   factId: "fact-1a2b3c4d5e6f",
 *   graph: "urn:coa:graph:asserted",
 *   object: {
 *     iri: "urn:coa:entity:archive",
 *     kind: "iri",
 *     value: "urn:coa:entity:archive"
 *   },
 *   predicate: "urn:coa:predicate:belongs-to",
 *   state: "active",
 *   subject: "urn:coa:entity:contract-ledger"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RestoreFactCommand extends $Command
  .classBuilder<
    RestoreFactCommandInput,
    RestoreFactCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RestoreFact", {})
  .n("ControlPlaneServiceClient", "RestoreFactCommand")
  .sc(RestoreFact$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RestoreFactInput;
      output: FactRecord;
    };
    sdk: {
      input: RestoreFactCommandInput;
      output: RestoreFactCommandOutput;
    };
  };
}
