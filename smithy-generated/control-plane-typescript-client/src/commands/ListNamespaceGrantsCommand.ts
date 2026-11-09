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
import type { ListNamespaceGrantsInput, ListNamespaceGrantsOutput } from "../models/models_0";
import { ListNamespaceGrants$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListNamespaceGrantsCommand}.
 */
export interface ListNamespaceGrantsCommandInput extends ListNamespaceGrantsInput {}
/**
 * @public
 *
 * The output of {@link ListNamespaceGrantsCommand}.
 */
export interface ListNamespaceGrantsCommandOutput extends ListNamespaceGrantsOutput, __MetadataBearer {}

/**
 * Lists the grants defined within a namespace, optionally filtered to a single
 * principal, with cursor-based pagination.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListNamespaceGrantsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListNamespaceGrantsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListNamespaceGrantsInput
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 *   namespaceId: "STRING_VALUE", // required
 *   principal: "STRING_VALUE",
 * };
 * const command = new ListNamespaceGrantsCommand(input);
 * const response = await client.send(command);
 * // { // ListNamespaceGrantsOutput
 * //   nextToken: "STRING_VALUE",
 * //   grants: [ // GrantSummaryList // required
 * //     { // GrantSummary
 * //       grantId: "STRING_VALUE", // required
 * //       namespaceId: "STRING_VALUE", // required
 * //       principalType: "User" || "Group" || "Agent", // required
 * //       principalId: "STRING_VALUE", // required
 * //       role: "STRING_VALUE", // required
 * //       grantedBy: "STRING_VALUE", // required
 * //       grantedAt: "STRING_VALUE", // required
 * //       tableAllowlist: [ // TableAllowlist
 * //         "STRING_VALUE",
 * //       ],
 * //       columnDenylist: { // ColumnDenylist
 * //         "<keys>": [ // ColumnList
 * //           "STRING_VALUE",
 * //         ],
 * //       },
 * //       allowedMetrics: [ // MetricsList
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListNamespaceGrantsCommandInput - {@link ListNamespaceGrantsCommandInput}
 * @returns {@link ListNamespaceGrantsCommandOutput}
 * @see {@link ListNamespaceGrantsCommandInput} for command's `input` shape.
 * @see {@link ListNamespaceGrantsCommandOutput} for command's `response` shape.
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
 * @example List grants in a namespace
 * ```javascript
 * //
 * const input = {
 *   maxResults: 25,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
 * };
 * const command = new ListNamespaceGrantsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   grants: [
 *     {
 *       grantId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *       grantedAt: "2026-01-15T10:30:00Z",
 *       grantedBy: "admin@example.com",
 *       namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *       principalId: "alice@example.com",
 *       principalType: "User",
 *       role: "namespace-editor"
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOjI1fQ=="
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListNamespaceGrantsCommand extends $Command
  .classBuilder<
    ListNamespaceGrantsCommandInput,
    ListNamespaceGrantsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListNamespaceGrants", {})
  .n("ControlPlaneServiceClient", "ListNamespaceGrantsCommand")
  .sc(ListNamespaceGrants$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListNamespaceGrantsInput;
      output: ListNamespaceGrantsOutput;
    };
    sdk: {
      input: ListNamespaceGrantsCommandInput;
      output: ListNamespaceGrantsCommandOutput;
    };
  };
}
