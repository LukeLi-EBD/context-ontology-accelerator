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
import type { GetCanvasManifestInput, GetCanvasManifestOutput } from "../models/models_0";
import { GetCanvasManifest$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetCanvasManifestCommand}.
 */
export interface GetCanvasManifestCommandInput extends GetCanvasManifestInput {}
/**
 * @public
 *
 * The output of {@link GetCanvasManifestCommand}.
 */
export interface GetCanvasManifestCommandOutput extends GetCanvasManifestOutput, __MetadataBearer {}

/**
 * Discover what the canvas can render, and its hard limits.
 *
 * The canvas reads this before requesting a subgraph so it can disable the
 * controls the backend cannot honour and label a capped result honestly,
 * instead of guessing the limits on the client.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetCanvasManifestCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetCanvasManifestCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetCanvasManifestInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new GetCanvasManifestCommand(input);
 * const response = await client.send(command);
 * // { // GetCanvasManifestOutput
 * //   capabilities: [ // CanvasCapabilityList // required
 * //     "STRING_VALUE",
 * //   ],
 * //   limits: { // CanvasLimits
 * //     maxNodes: Number("int"), // required
 * //     maxEdges: Number("int"), // required
 * //     maxPageSize: Number("int"), // required
 * //   },
 * // };
 *
 * ```
 *
 * @param GetCanvasManifestCommandInput - {@link GetCanvasManifestCommandInput}
 * @returns {@link GetCanvasManifestCommandOutput}
 * @see {@link GetCanvasManifestCommandInput} for command's `input` shape.
 * @see {@link GetCanvasManifestCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
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
 * @example Read the canvas capabilities and limits
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetCanvasManifestCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   capabilities: [
 *     "nodeKinds",
 *     "graphFilter",
 *     "offsetPaging"
 *   ],
 *   limits: {
 *     maxEdges: 400,
 *     maxNodes: 200,
 *     maxPageSize: 100
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetCanvasManifestCommand extends $Command
  .classBuilder<
    GetCanvasManifestCommandInput,
    GetCanvasManifestCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetCanvasManifest", {})
  .n("ControlPlaneServiceClient", "GetCanvasManifestCommand")
  .sc(GetCanvasManifest$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetCanvasManifestInput;
      output: GetCanvasManifestOutput;
    };
    sdk: {
      input: GetCanvasManifestCommandInput;
      output: GetCanvasManifestCommandOutput;
    };
  };
}
