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
import type { DeleteGrantInput, DeleteGrantOutput } from "../models/models_0";
import { DeleteGrant$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteGrantCommand}.
 */
export interface DeleteGrantCommandInput extends DeleteGrantInput {}
/**
 * @public
 *
 * The output of {@link DeleteGrantCommand}.
 */
export interface DeleteGrantCommandOutput extends DeleteGrantOutput, __MetadataBearer {}

/**
 * Revokes a namespace grant by id, removing the principal's role and any
 * associated data-access scoping within the namespace.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, DeleteGrantCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, DeleteGrantCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // DeleteGrantInput
 *   namespaceId: "STRING_VALUE", // required
 *   grantId: "STRING_VALUE", // required
 * };
 * const command = new DeleteGrantCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteGrantCommandInput - {@link DeleteGrantCommandInput}
 * @returns {@link DeleteGrantCommandOutput}
 * @see {@link DeleteGrantCommandInput} for command's `input` shape.
 * @see {@link DeleteGrantCommandOutput} for command's `response` shape.
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
 * @example Delete a namespace grant
 * ```javascript
 * //
 * const input = {
 *   grantId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
 * };
 * const command = new DeleteGrantCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* empty *\/ }
 * *\/
 * ```
 *
 * @public
 */
export class DeleteGrantCommand extends $Command
  .classBuilder<
    DeleteGrantCommandInput,
    DeleteGrantCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "DeleteGrant", {})
  .n("ControlPlaneServiceClient", "DeleteGrantCommand")
  .sc(DeleteGrant$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DeleteGrantInput;
      output: {};
    };
    sdk: {
      input: DeleteGrantCommandInput;
      output: DeleteGrantCommandOutput;
    };
  };
}
