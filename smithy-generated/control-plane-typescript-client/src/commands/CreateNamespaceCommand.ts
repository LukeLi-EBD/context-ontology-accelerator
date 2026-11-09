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
import type { CreateNamespaceInput, CreateNamespaceOutput } from "../models/models_0";
import { CreateNamespace$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateNamespaceCommand}.
 */
export interface CreateNamespaceCommandInput extends CreateNamespaceInput {}
/**
 * @public
 *
 * The output of {@link CreateNamespaceCommand}.
 */
export interface CreateNamespaceCommandOutput extends CreateNamespaceOutput, __MetadataBearer {}

/**
 * Create a new namespace to hold data sources, ontologies, and grants.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, CreateNamespaceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, CreateNamespaceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // CreateNamespaceInput
 *   name: "STRING_VALUE", // required
 *   displayName: "STRING_VALUE",
 *   description: "STRING_VALUE",
 *   owner: "STRING_VALUE", // required
 *   language: "STRING_VALUE",
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new CreateNamespaceCommand(input);
 * const response = await client.send(command);
 * // { // CreateNamespaceOutput
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
 * @param CreateNamespaceCommandInput - {@link CreateNamespaceCommandInput}
 * @returns {@link CreateNamespaceCommandOutput}
 * @see {@link CreateNamespaceCommandInput} for command's `input` shape.
 * @see {@link CreateNamespaceCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
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
 * @example Create a sales analytics namespace
 * ```javascript
 * //
 * const input = {
 *   description: "Q3 revenue data and dashboards",
 *   displayName: "Sales Analytics",
 *   language: "ja",
 *   name: "sales-analytics",
 *   owner: "data-team@example.com"
 * };
 * const command = new CreateNamespaceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   namespace: {
 *     createdAt: "2026-07-23T14:30:00Z",
 *     description: "Q3 revenue data and dashboards",
 *     displayName: "Sales Analytics",
 *     language: "ja",
 *     name: "sales-analytics",
 *     namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *     owner: "data-team@example.com",
 *     status: "ACTIVE"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CreateNamespaceCommand extends $Command
  .classBuilder<
    CreateNamespaceCommandInput,
    CreateNamespaceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "CreateNamespace", {})
  .n("ControlPlaneServiceClient", "CreateNamespaceCommand")
  .sc(CreateNamespace$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CreateNamespaceInput;
      output: CreateNamespaceOutput;
    };
    sdk: {
      input: CreateNamespaceCommandInput;
      output: CreateNamespaceCommandOutput;
    };
  };
}
