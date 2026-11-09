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
import type { DeletePlatformGrantInput, DeletePlatformGrantOutput } from "../models/models_0";
import { DeletePlatformGrant$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeletePlatformGrantCommand}.
 */
export interface DeletePlatformGrantCommandInput extends DeletePlatformGrantInput {}
/**
 * @public
 *
 * The output of {@link DeletePlatformGrantCommand}.
 */
export interface DeletePlatformGrantCommandOutput extends DeletePlatformGrantOutput, __MetadataBearer {}

/**
 * Revokes a platform-scoped grant by id, removing the principal's platform
 * role across all namespaces.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, DeletePlatformGrantCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, DeletePlatformGrantCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // DeletePlatformGrantInput
 *   grantId: "STRING_VALUE", // required
 * };
 * const command = new DeletePlatformGrantCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeletePlatformGrantCommandInput - {@link DeletePlatformGrantCommandInput}
 * @returns {@link DeletePlatformGrantCommandOutput}
 * @see {@link DeletePlatformGrantCommandInput} for command's `input` shape.
 * @see {@link DeletePlatformGrantCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
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
 * @example Delete a platform grant
 * ```javascript
 * //
 * const input = {
 *   grantId: "01HZY8K3M4N5P6Q7R8S9T0V1W2"
 * };
 * const command = new DeletePlatformGrantCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* empty *\/ }
 * *\/
 * ```
 *
 * @public
 */
export class DeletePlatformGrantCommand extends $Command
  .classBuilder<
    DeletePlatformGrantCommandInput,
    DeletePlatformGrantCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "DeletePlatformGrant", {})
  .n("ControlPlaneServiceClient", "DeletePlatformGrantCommand")
  .sc(DeletePlatformGrant$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DeletePlatformGrantInput;
      output: {};
    };
    sdk: {
      input: DeletePlatformGrantCommandInput;
      output: DeletePlatformGrantCommandOutput;
    };
  };
}
