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
import type { PutSourceRescanScheduleInput, PutSourceRescanScheduleOutput } from "../models/models_1";
import { PutSourceRescanSchedule$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link PutSourceRescanScheduleCommand}.
 */
export interface PutSourceRescanScheduleCommandInput extends PutSourceRescanScheduleInput {}
/**
 * @public
 *
 * The output of {@link PutSourceRescanScheduleCommand}.
 */
export interface PutSourceRescanScheduleCommandOutput extends PutSourceRescanScheduleOutput, __MetadataBearer {}

/**
 * Configure (or disable) the recurring rescan schedule for a DATABASE source.
 * Setting enabled=true with a scheduleExpression creates or updates an
 * EventBridge schedule that fires a SCHEDULED rescan on that cadence; setting
 * enabled=false removes it.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, PutSourceRescanScheduleCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, PutSourceRescanScheduleCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // PutSourceRescanScheduleInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   enabled: true || false, // required
 *   scheduleExpression: "STRING_VALUE",
 *   timezone: "STRING_VALUE",
 * };
 * const command = new PutSourceRescanScheduleCommand(input);
 * const response = await client.send(command);
 * // { // PutSourceRescanScheduleOutput
 * //   sourceId: "STRING_VALUE", // required
 * //   rescanSchedule: { // RescanSchedule
 * //     enabled: true || false, // required
 * //     scheduleExpression: "STRING_VALUE",
 * //     timezone: "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param PutSourceRescanScheduleCommandInput - {@link PutSourceRescanScheduleCommandInput}
 * @returns {@link PutSourceRescanScheduleCommandOutput}
 * @see {@link PutSourceRescanScheduleCommandInput} for command's `input` shape.
 * @see {@link PutSourceRescanScheduleCommandOutput} for command's `response` shape.
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
 * @example Enable a nightly rescan
 * ```javascript
 * //
 * const input = {
 *   enabled: true,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   scheduleExpression: "cron(0 3 * * ? *)",
 *   sourceId: "src-7f3a9c1e",
 *   timezone: "America/New_York"
 * };
 * const command = new PutSourceRescanScheduleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   rescanSchedule: {
 *     enabled: true,
 *     scheduleExpression: "cron(0 3 * * ? *)",
 *     timezone: "America/New_York"
 *   },
 *   sourceId: "src-7f3a9c1e"
 * }
 * *\/
 * ```
 *
 * @example Disable the recurring rescan
 * ```javascript
 * //
 * const input = {
 *   enabled: false,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new PutSourceRescanScheduleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   rescanSchedule: {
 *     enabled: false
 *   },
 *   sourceId: "src-7f3a9c1e"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class PutSourceRescanScheduleCommand extends $Command
  .classBuilder<
    PutSourceRescanScheduleCommandInput,
    PutSourceRescanScheduleCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "PutSourceRescanSchedule", {})
  .n("ControlPlaneServiceClient", "PutSourceRescanScheduleCommand")
  .sc(PutSourceRescanSchedule$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: PutSourceRescanScheduleInput;
      output: PutSourceRescanScheduleOutput;
    };
    sdk: {
      input: PutSourceRescanScheduleCommandInput;
      output: PutSourceRescanScheduleCommandOutput;
    };
  };
}
