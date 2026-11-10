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
import type { ListNamespaceRolesInput, ListNamespaceRolesOutput } from "../models/models_1";
import { ListNamespaceRoles$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListNamespaceRolesCommand}.
 */
export interface ListNamespaceRolesCommandInput extends ListNamespaceRolesInput {}
/**
 * @public
 *
 * The output of {@link ListNamespaceRolesCommand}.
 */
export interface ListNamespaceRolesCommandOutput extends ListNamespaceRolesOutput, __MetadataBearer {}

/**
 * List the roles available within a specific namespace. Not paginated: the
 * role set is small and fixed (see `RoleSummaryList`).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListNamespaceRolesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListNamespaceRolesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListNamespaceRolesInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new ListNamespaceRolesCommand(input);
 * const response = await client.send(command);
 * // { // ListNamespaceRolesOutput
 * //   roles: [ // RoleSummaryList // required
 * //     { // RoleSummary
 * //       roleId: "STRING_VALUE", // required
 * //       name: "STRING_VALUE", // required
 * //       description: "STRING_VALUE",
 * //       scope: "PLATFORM" || "NAMESPACE", // required
 * //       isBuiltIn: true || false, // required
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListNamespaceRolesCommandInput - {@link ListNamespaceRolesCommandInput}
 * @returns {@link ListNamespaceRolesCommandOutput}
 * @see {@link ListNamespaceRolesCommandInput} for command's `input` shape.
 * @see {@link ListNamespaceRolesCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
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
 * @example List namespace roles
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "550e8400-e29b-41d4-a716-446655440000"
 * };
 * const command = new ListNamespaceRolesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   roles: [
 *     {
 *       description: "Manage all resources within the namespace.",
 *       isBuiltIn: true,
 *       name: "namespace-admin",
 *       roleId: "01H8XGJWBWBAQ4Z2X3Y5N6P7Q",
 *       scope: "NAMESPACE"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListNamespaceRolesCommand extends $Command
  .classBuilder<
    ListNamespaceRolesCommandInput,
    ListNamespaceRolesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListNamespaceRoles", {})
  .n("ControlPlaneServiceClient", "ListNamespaceRolesCommand")
  .sc(ListNamespaceRoles$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListNamespaceRolesInput;
      output: ListNamespaceRolesOutput;
    };
    sdk: {
      input: ListNamespaceRolesCommandInput;
      output: ListNamespaceRolesCommandOutput;
    };
  };
}
