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
import type { ListPlatformGrantsInput, ListPlatformGrantsOutput } from "../models/models_0";
import { ListPlatformGrants$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListPlatformGrantsCommand}.
 */
export interface ListPlatformGrantsCommandInput extends ListPlatformGrantsInput {}
/**
 * @public
 *
 * The output of {@link ListPlatformGrantsCommand}.
 */
export interface ListPlatformGrantsCommandOutput extends ListPlatformGrantsOutput, __MetadataBearer {}

/**
 * Lists platform-scoped grants, optionally filtered to a single principal,
 * with cursor-based pagination.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListPlatformGrantsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListPlatformGrantsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListPlatformGrantsInput
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 *   principal: "STRING_VALUE",
 * };
 * const command = new ListPlatformGrantsCommand(input);
 * const response = await client.send(command);
 * // { // ListPlatformGrantsOutput
 * //   nextToken: "STRING_VALUE",
 * //   grants: [ // PlatformGrantSummaryList // required
 * //     { // PlatformGrantSummary
 * //       grantId: "STRING_VALUE", // required
 * //       principalType: "User" || "Group" || "Agent", // required
 * //       principalId: "STRING_VALUE", // required
 * //       role: "STRING_VALUE", // required
 * //       grantedBy: "STRING_VALUE", // required
 * //       grantedAt: "STRING_VALUE", // required
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListPlatformGrantsCommandInput - {@link ListPlatformGrantsCommandInput}
 * @returns {@link ListPlatformGrantsCommandOutput}
 * @see {@link ListPlatformGrantsCommandInput} for command's `input` shape.
 * @see {@link ListPlatformGrantsCommandOutput} for command's `response` shape.
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
 * @example List platform grants
 * ```javascript
 * //
 * const input = {
 *   maxResults: 25
 * };
 * const command = new ListPlatformGrantsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   grants: [
 *     {
 *       grantId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *       grantedAt: "2026-01-15T10:30:00Z",
 *       grantedBy: "admin@example.com",
 *       principalId: "platform-operators",
 *       principalType: "Group",
 *       role: "platform-admin"
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOjI1fQ=="
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListPlatformGrantsCommand extends $Command
  .classBuilder<
    ListPlatformGrantsCommandInput,
    ListPlatformGrantsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListPlatformGrants", {})
  .n("ControlPlaneServiceClient", "ListPlatformGrantsCommand")
  .sc(ListPlatformGrants$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListPlatformGrantsInput;
      output: ListPlatformGrantsOutput;
    };
    sdk: {
      input: ListPlatformGrantsCommandInput;
      output: ListPlatformGrantsCommandOutput;
    };
  };
}
