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
import type { CreatePlatformGrantInput, CreatePlatformGrantOutput } from "../models/models_0";
import { CreatePlatformGrant$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreatePlatformGrantCommand}.
 */
export interface CreatePlatformGrantCommandInput extends CreatePlatformGrantInput {}
/**
 * @public
 *
 * The output of {@link CreatePlatformGrantCommand}.
 */
export interface CreatePlatformGrantCommandOutput extends CreatePlatformGrantOutput, __MetadataBearer {}

/**
 * Binds a principal to a platform-scoped role that applies across all
 * namespaces. The role must already exist as a platform role.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, CreatePlatformGrantCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, CreatePlatformGrantCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // CreatePlatformGrantInput
 *   body: { // CreatePlatformGrantRequest
 *     principalType: "User" || "Group" || "Agent", // required
 *     principalId: "STRING_VALUE", // required
 *     role: "STRING_VALUE", // required
 *     clientToken: "STRING_VALUE",
 *   },
 * };
 * const command = new CreatePlatformGrantCommand(input);
 * const response = await client.send(command);
 * // { // CreatePlatformGrantOutput
 * //   grant: { // PlatformGrantSummary
 * //     grantId: "STRING_VALUE", // required
 * //     principalType: "User" || "Group" || "Agent", // required
 * //     principalId: "STRING_VALUE", // required
 * //     role: "STRING_VALUE", // required
 * //     grantedBy: "STRING_VALUE", // required
 * //     grantedAt: "STRING_VALUE", // required
 * //   },
 * // };
 *
 * ```
 *
 * @param CreatePlatformGrantCommandInput - {@link CreatePlatformGrantCommandInput}
 * @returns {@link CreatePlatformGrantCommandOutput}
 * @see {@link CreatePlatformGrantCommandInput} for command's `input` shape.
 * @see {@link CreatePlatformGrantCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Grant a group the platform-admin role
 * ```javascript
 * //
 * const input = {
 *   body: {
 *     principalId: "platform-operators",
 *     principalType: "Group",
 *     role: "platform-admin"
 *   }
 * };
 * const command = new CreatePlatformGrantCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   grant: {
 *     grantId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *     grantedAt: "2026-01-15T10:30:00Z",
 *     grantedBy: "admin@example.com",
 *     principalId: "platform-operators",
 *     principalType: "Group",
 *     role: "platform-admin"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CreatePlatformGrantCommand extends $Command
  .classBuilder<
    CreatePlatformGrantCommandInput,
    CreatePlatformGrantCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "CreatePlatformGrant", {})
  .n("ControlPlaneServiceClient", "CreatePlatformGrantCommand")
  .sc(CreatePlatformGrant$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CreatePlatformGrantInput;
      output: CreatePlatformGrantOutput;
    };
    sdk: {
      input: CreatePlatformGrantCommandInput;
      output: CreatePlatformGrantCommandOutput;
    };
  };
}
