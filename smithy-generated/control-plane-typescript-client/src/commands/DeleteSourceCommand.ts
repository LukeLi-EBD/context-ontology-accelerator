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
import type { DeleteSourceInput, DeleteSourceOutput } from "../models/models_0";
import { DeleteSource$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteSourceCommand}.
 */
export interface DeleteSourceCommandInput extends DeleteSourceInput {}
/**
 * @public
 *
 * The output of {@link DeleteSourceCommand}.
 */
export interface DeleteSourceCommandOutput extends DeleteSourceOutput, __MetadataBearer {}

/**
 * Delete a source and all associated data.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, DeleteSourceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, DeleteSourceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // DeleteSourceInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 * };
 * const command = new DeleteSourceCommand(input);
 * const response = await client.send(command);
 * // { // DeleteSourceOutput
 * //   sourceId: "STRING_VALUE",
 * //   status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED",
 * // };
 *
 * ```
 *
 * @param DeleteSourceCommandInput - {@link DeleteSourceCommandInput}
 * @returns {@link DeleteSourceCommandOutput}
 * @see {@link DeleteSourceCommandInput} for command's `input` shape.
 * @see {@link DeleteSourceCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
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
 * @example Delete a source
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new DeleteSourceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   sourceId: "src-7f3a9c1e",
 *   status: "DELETING"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class DeleteSourceCommand extends $Command
  .classBuilder<
    DeleteSourceCommandInput,
    DeleteSourceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "DeleteSource", {})
  .n("ControlPlaneServiceClient", "DeleteSourceCommand")
  .sc(DeleteSource$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DeleteSourceInput;
      output: DeleteSourceOutput;
    };
    sdk: {
      input: DeleteSourceCommandInput;
      output: DeleteSourceCommandOutput;
    };
  };
}
