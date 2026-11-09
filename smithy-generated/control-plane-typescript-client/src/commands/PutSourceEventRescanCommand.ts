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
import type { PutSourceEventRescanInput, PutSourceEventRescanOutput } from "../models/models_0";
import { PutSourceEventRescan$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link PutSourceEventRescanCommand}.
 */
export interface PutSourceEventRescanCommandInput extends PutSourceEventRescanInput {}
/**
 * @public
 *
 * The output of {@link PutSourceEventRescanCommand}.
 */
export interface PutSourceEventRescanCommandOutput extends PutSourceEventRescanOutput, __MetadataBearer {}

/**
 * Enable or disable event-driven rescans for a DATABASE source (Glue only).
 * When enabled, an EventBridge rule matching the source's Glue Data Catalog
 * changes fires an EVENT rescan; disabling removes the rule.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, PutSourceEventRescanCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, PutSourceEventRescanCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // PutSourceEventRescanInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   enabled: true || false, // required
 * };
 * const command = new PutSourceEventRescanCommand(input);
 * const response = await client.send(command);
 * // { // PutSourceEventRescanOutput
 * //   sourceId: "STRING_VALUE", // required
 * //   eventRescan: { // EventRescanConfig
 * //     enabled: true || false, // required
 * //   },
 * // };
 *
 * ```
 *
 * @param PutSourceEventRescanCommandInput - {@link PutSourceEventRescanCommandInput}
 * @returns {@link PutSourceEventRescanCommandOutput}
 * @see {@link PutSourceEventRescanCommandInput} for command's `input` shape.
 * @see {@link PutSourceEventRescanCommandOutput} for command's `response` shape.
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
 * @example Enable event-driven rescans
 * ```javascript
 * //
 * const input = {
 *   enabled: true,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new PutSourceEventRescanCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   eventRescan: {
 *     enabled: true
 *   },
 *   sourceId: "src-7f3a9c1e"
 * }
 * *\/
 * ```
 *
 * @example Disable event-driven rescans
 * ```javascript
 * //
 * const input = {
 *   enabled: false,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new PutSourceEventRescanCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   eventRescan: {
 *     enabled: false
 *   },
 *   sourceId: "src-7f3a9c1e"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class PutSourceEventRescanCommand extends $Command
  .classBuilder<
    PutSourceEventRescanCommandInput,
    PutSourceEventRescanCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "PutSourceEventRescan", {})
  .n("ControlPlaneServiceClient", "PutSourceEventRescanCommand")
  .sc(PutSourceEventRescan$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: PutSourceEventRescanInput;
      output: PutSourceEventRescanOutput;
    };
    sdk: {
      input: PutSourceEventRescanCommandInput;
      output: PutSourceEventRescanCommandOutput;
    };
  };
}
