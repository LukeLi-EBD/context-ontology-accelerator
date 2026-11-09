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
import type { CreateGrantInput, CreateGrantOutput } from "../models/models_0";
import { CreateGrant$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateGrantCommand}.
 */
export interface CreateGrantCommandInput extends CreateGrantInput {}
/**
 * @public
 *
 * The output of {@link CreateGrantCommand}.
 */
export interface CreateGrantCommandOutput extends CreateGrantOutput, __MetadataBearer {}

/**
 * Grants a principal a role within a namespace, optionally scoping data access
 * via a table allowlist, column denylist, and allowed-metrics list.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, CreateGrantCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, CreateGrantCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // CreateGrantInput
 *   namespaceId: "STRING_VALUE", // required
 *   body: { // CreateGrantRequest
 *     principalType: "User" || "Group" || "Agent", // required
 *     principalId: "STRING_VALUE", // required
 *     role: "STRING_VALUE", // required
 *     tableAllowlist: [ // TableAllowlist
 *       "STRING_VALUE",
 *     ],
 *     columnDenylist: { // ColumnDenylist
 *       "<keys>": [ // ColumnList
 *         "STRING_VALUE",
 *       ],
 *     },
 *     allowedMetrics: [ // MetricsList
 *       "STRING_VALUE",
 *     ],
 *     clientToken: "STRING_VALUE",
 *   },
 * };
 * const command = new CreateGrantCommand(input);
 * const response = await client.send(command);
 * // { // CreateGrantOutput
 * //   grant: { // GrantSummary
 * //     grantId: "STRING_VALUE", // required
 * //     namespaceId: "STRING_VALUE", // required
 * //     principalType: "User" || "Group" || "Agent", // required
 * //     principalId: "STRING_VALUE", // required
 * //     role: "STRING_VALUE", // required
 * //     grantedBy: "STRING_VALUE", // required
 * //     grantedAt: "STRING_VALUE", // required
 * //     tableAllowlist: [ // TableAllowlist
 * //       "STRING_VALUE",
 * //     ],
 * //     columnDenylist: { // ColumnDenylist
 * //       "<keys>": [ // ColumnList
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //     allowedMetrics: [ // MetricsList
 * //       "STRING_VALUE",
 * //     ],
 * //   },
 * // };
 *
 * ```
 *
 * @param CreateGrantCommandInput - {@link CreateGrantCommandInput}
 * @returns {@link CreateGrantCommandOutput}
 * @see {@link CreateGrantCommandInput} for command's `input` shape.
 * @see {@link CreateGrantCommandOutput} for command's `response` shape.
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
 * @example Grant a user the editor role on a namespace
 * ```javascript
 * //
 * const input = {
 *   body: {
 *     allowedMetrics: [
 *       "total_revenue"
 *     ],
 *     columnDenylist: {
 *       sales.customers: [
 *         "ssn",
 *         "email"
 *       ]
 *     },
 *     principalId: "alice@example.com",
 *     principalType: "User",
 *     role: "namespace-editor",
 *     tableAllowlist: [
 *       "sales.orders",
 *       "sales.customers"
 *     ]
 *   },
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
 * };
 * const command = new CreateGrantCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   grant: {
 *     allowedMetrics: [
 *       "total_revenue"
 *     ],
 *     columnDenylist: {
 *       sales.customers: [
 *         "ssn",
 *         "email"
 *       ]
 *     },
 *     grantId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *     grantedAt: "2026-01-15T10:30:00Z",
 *     grantedBy: "admin@example.com",
 *     namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *     principalId: "alice@example.com",
 *     principalType: "User",
 *     role: "namespace-editor",
 *     tableAllowlist: [
 *       "sales.orders",
 *       "sales.customers"
 *     ]
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CreateGrantCommand extends $Command
  .classBuilder<
    CreateGrantCommandInput,
    CreateGrantCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "CreateGrant", {})
  .n("ControlPlaneServiceClient", "CreateGrantCommand")
  .sc(CreateGrant$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CreateGrantInput;
      output: CreateGrantOutput;
    };
    sdk: {
      input: CreateGrantCommandInput;
      output: CreateGrantCommandOutput;
    };
  };
}
