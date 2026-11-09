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
import type { ListNamespacesInput, ListNamespacesOutput } from "../models/models_0";
import { ListNamespaces$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListNamespacesCommand}.
 */
export interface ListNamespacesCommandInput extends ListNamespacesInput {}
/**
 * @public
 *
 * The output of {@link ListNamespacesCommand}.
 */
export interface ListNamespacesCommandOutput extends ListNamespacesOutput, __MetadataBearer {}

/**
 * List namespaces the caller can access, with optional pagination.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListNamespacesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListNamespacesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListNamespacesInput
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListNamespacesCommand(input);
 * const response = await client.send(command);
 * // { // ListNamespacesOutput
 * //   nextToken: "STRING_VALUE",
 * //   namespaces: [ // NamespaceSummaryList // required
 * //     { // NamespaceSummary
 * //       namespaceId: "STRING_VALUE", // required
 * //       name: "STRING_VALUE", // required
 * //       displayName: "STRING_VALUE",
 * //       status: "ACTIVE" || "ARCHIVED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * //       language: "STRING_VALUE", // required
 * //       sourceCount: Number("int"),
 * //       createdAt: "STRING_VALUE",
 * //       updatedAt: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListNamespacesCommandInput - {@link ListNamespacesCommandInput}
 * @returns {@link ListNamespacesCommandOutput}
 * @see {@link ListNamespacesCommandInput} for command's `input` shape.
 * @see {@link ListNamespacesCommandOutput} for command's `response` shape.
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
 * @example List namespaces (first page)
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20
 * };
 * const command = new ListNamespacesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   namespaces: [
 *     {
 *       createdAt: "2026-07-23T14:30:00Z",
 *       displayName: "Sales Analytics",
 *       language: "en",
 *       name: "sales-analytics",
 *       namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *       sourceCount: 3,
 *       status: "ACTIVE",
 *       updatedAt: "2026-07-23T15:00:00Z"
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOiAyMH0="
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListNamespacesCommand extends $Command
  .classBuilder<
    ListNamespacesCommandInput,
    ListNamespacesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListNamespaces", {})
  .n("ControlPlaneServiceClient", "ListNamespacesCommand")
  .sc(ListNamespaces$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListNamespacesInput;
      output: ListNamespacesOutput;
    };
    sdk: {
      input: ListNamespacesCommandInput;
      output: ListNamespacesCommandOutput;
    };
  };
}
