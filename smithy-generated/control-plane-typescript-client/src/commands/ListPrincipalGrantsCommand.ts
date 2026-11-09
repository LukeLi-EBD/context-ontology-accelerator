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
import type { ListPrincipalGrantsInput, ListPrincipalGrantsOutput } from "../models/models_0";
import { ListPrincipalGrants$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListPrincipalGrantsCommand}.
 */
export interface ListPrincipalGrantsCommandInput extends ListPrincipalGrantsInput {}
/**
 * @public
 *
 * The output of {@link ListPrincipalGrantsCommand}.
 */
export interface ListPrincipalGrantsCommandOutput extends ListPrincipalGrantsOutput, __MetadataBearer {}

/**
 * Lists the namespace grants held by a single principal (and the groups it
 * belongs to) across all namespaces, with cursor-based pagination. Only the
 * `me` principal (the caller) is accepted. The default page size is the
 * maximum, so a caller holding up to 1,000 grants gets them all in one page.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListPrincipalGrantsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListPrincipalGrantsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListPrincipalGrantsInput
 *   principalId: "STRING_VALUE", // required
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListPrincipalGrantsCommand(input);
 * const response = await client.send(command);
 * // { // ListPrincipalGrantsOutput
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
 * @param ListPrincipalGrantsCommandInput - {@link ListPrincipalGrantsCommandInput}
 * @returns {@link ListPrincipalGrantsCommandOutput}
 * @see {@link ListPrincipalGrantsCommandInput} for command's `input` shape.
 * @see {@link ListPrincipalGrantsCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
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
 * @example List all grants for a principal
 * ```javascript
 * //
 * const input = {
 *   principalId: "alice@example.com"
 * };
 * const command = new ListPrincipalGrantsCommand(input);
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
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListPrincipalGrantsCommand extends $Command
  .classBuilder<
    ListPrincipalGrantsCommandInput,
    ListPrincipalGrantsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListPrincipalGrants", {})
  .n("ControlPlaneServiceClient", "ListPrincipalGrantsCommand")
  .sc(ListPrincipalGrants$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListPrincipalGrantsInput;
      output: ListPrincipalGrantsOutput;
    };
    sdk: {
      input: ListPrincipalGrantsCommandInput;
      output: ListPrincipalGrantsCommandOutput;
    };
  };
}
