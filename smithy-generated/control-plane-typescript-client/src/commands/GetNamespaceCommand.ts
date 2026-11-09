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
import type { GetNamespaceInput, GetNamespaceOutput } from "../models/models_0";
import { GetNamespace$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetNamespaceCommand}.
 */
export interface GetNamespaceCommandInput extends GetNamespaceInput {}
/**
 * @public
 *
 * The output of {@link GetNamespaceCommand}.
 */
export interface GetNamespaceCommandOutput extends GetNamespaceOutput, __MetadataBearer {}

/**
 * Retrieve the full detail of a single namespace by its identifier.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetNamespaceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetNamespaceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetNamespaceInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new GetNamespaceCommand(input);
 * const response = await client.send(command);
 * // { // GetNamespaceOutput
 * //   namespace: { // NamespaceDetail
 * //     namespaceId: "STRING_VALUE", // required
 * //     name: "STRING_VALUE", // required
 * //     displayName: "STRING_VALUE",
 * //     description: "STRING_VALUE",
 * //     owner: "STRING_VALUE", // required
 * //     status: "ACTIVE" || "ARCHIVED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * //     language: "STRING_VALUE", // required
 * //     dataZoneProjectId: "STRING_VALUE",
 * //     sourceCount: Number("int"),
 * //     createdAt: "STRING_VALUE", // required
 * //     updatedAt: "STRING_VALUE",
 * //     athenaWorkgroupName: "STRING_VALUE",
 * //     datasourceExternalId: "STRING_VALUE",
 * //     vkgHealth: "HEALTHY" || "DEGRADED" || "UNAVAILABLE" || "PROVISIONING" || "UNKNOWN",
 * //     vkgHealthReason: "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param GetNamespaceCommandInput - {@link GetNamespaceCommandInput}
 * @returns {@link GetNamespaceCommandOutput}
 * @see {@link GetNamespaceCommandInput} for command's `input` shape.
 * @see {@link GetNamespaceCommandOutput} for command's `response` shape.
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
 * @example Get a namespace by ID
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetNamespaceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   namespace: {
 *     createdAt: "2026-07-23T14:30:00Z",
 *     description: "Q3 revenue data and dashboards",
 *     displayName: "Sales Analytics",
 *     language: "en",
 *     name: "sales-analytics",
 *     namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *     owner: "data-team@example.com",
 *     sourceCount: 3,
 *     status: "ACTIVE",
 *     updatedAt: "2026-07-23T15:00:00Z"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetNamespaceCommand extends $Command
  .classBuilder<
    GetNamespaceCommandInput,
    GetNamespaceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetNamespace", {})
  .n("ControlPlaneServiceClient", "GetNamespaceCommand")
  .sc(GetNamespace$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetNamespaceInput;
      output: GetNamespaceOutput;
    };
    sdk: {
      input: GetNamespaceCommandInput;
      output: GetNamespaceCommandOutput;
    };
  };
}
