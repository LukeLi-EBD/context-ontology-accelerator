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
import type { FactUndoResult, UndoFactConflictResolutionInput } from "../models/models_0";
import { UndoFactConflictResolution$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UndoFactConflictResolutionCommand}.
 */
export interface UndoFactConflictResolutionCommandInput extends UndoFactConflictResolutionInput {}
/**
 * @public
 *
 * The output of {@link UndoFactConflictResolutionCommand}.
 */
export interface UndoFactConflictResolutionCommandOutput extends FactUndoResult, __MetadataBearer {}

/**
 * Undo the effective adjudication of one conflict group.
 *
 * Identify the group either by `eventId` (the adjudication event) or by
 * `subject` + `predicate`. `dryRun` is the safe default: it reports the rows
 * and values the undo would change without writing.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UndoFactConflictResolutionCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UndoFactConflictResolutionCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UndoFactConflictResolutionInput
 *   namespaceId: "STRING_VALUE", // required
 *   eventId: Number("int"),
 *   subject: "STRING_VALUE",
 *   predicate: "STRING_VALUE",
 *   actor: "STRING_VALUE",
 *   reason: "STRING_VALUE",
 *   dryRun: true || false,
 * };
 * const command = new UndoFactConflictResolutionCommand(input);
 * const response = await client.send(command);
 * // { // FactUndoResult
 * //   dryRun: true || false, // required
 * //   eventId: Number("int"),
 * //   subject: "STRING_VALUE", // required
 * //   predicate: "STRING_VALUE", // required
 * //   undoneAction: "STRING_VALUE", // required
 * //   restoredFactIds: [ // FactIdList
 * //     "STRING_VALUE",
 * //   ],
 * //   mergedFactId: "STRING_VALUE",
 * //   values: [ // FactIriList
 * //     "STRING_VALUE",
 * //   ],
 * //   conflict: true || false,
 * // };
 *
 * ```
 *
 * @param UndoFactConflictResolutionCommandInput - {@link UndoFactConflictResolutionCommandInput}
 * @returns {@link UndoFactConflictResolutionCommandOutput}
 * @see {@link UndoFactConflictResolutionCommandInput} for command's `input` shape.
 * @see {@link UndoFactConflictResolutionCommandOutput} for command's `response` shape.
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
 * @example Preview undoing a keep decision
 * ```javascript
 * //
 * const input = {
 *   actor: "operator",
 *   dryRun: true,
 *   eventId: 41,
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   reason: "wrong value kept"
 * };
 * const command = new UndoFactConflictResolutionCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   conflict: true,
 *   dryRun: true,
 *   predicate: "urn:coa:predicate:belongs-to",
 *   restoredFactIds: [
 *     "fact-0f1e2d3c4b5a"
 *   ],
 *   subject: "urn:coa:entity:contract-ledger",
 *   undoneAction: "keep",
 *   values: [
 *     "urn:coa:entity:archive",
 *     "urn:coa:entity:legal"
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UndoFactConflictResolutionCommand extends $Command
  .classBuilder<
    UndoFactConflictResolutionCommandInput,
    UndoFactConflictResolutionCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UndoFactConflictResolution", {})
  .n("ControlPlaneServiceClient", "UndoFactConflictResolutionCommand")
  .sc(UndoFactConflictResolution$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UndoFactConflictResolutionInput;
      output: FactUndoResult;
    };
    sdk: {
      input: UndoFactConflictResolutionCommandInput;
      output: UndoFactConflictResolutionCommandOutput;
    };
  };
}
