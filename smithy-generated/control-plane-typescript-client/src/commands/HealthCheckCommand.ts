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
import type { HealthCheckOutput } from "../models/models_0";
import { HealthCheck$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link HealthCheckCommand}.
 */
export interface HealthCheckCommandInput {}
/**
 * @public
 *
 * The output of {@link HealthCheckCommand}.
 */
export interface HealthCheckCommandOutput extends HealthCheckOutput, __MetadataBearer {}

/**
 * Lightweight liveness probe that reports whether the service is up.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, HealthCheckCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, HealthCheckCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = {};
 * const command = new HealthCheckCommand(input);
 * const response = await client.send(command);
 * // { // HealthCheckOutput
 * //   status: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param HealthCheckCommandInput - {@link HealthCheckCommandInput}
 * @returns {@link HealthCheckCommandOutput}
 * @see {@link HealthCheckCommandInput} for command's `input` shape.
 * @see {@link HealthCheckCommandOutput} for command's `response` shape.
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
 * @example Service is healthy
 * ```javascript
 * //
 * const input = { /* empty *\/ };
 * const command = new HealthCheckCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   status: "ok"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class HealthCheckCommand extends $Command
  .classBuilder<
    HealthCheckCommandInput,
    HealthCheckCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "HealthCheck", {})
  .n("ControlPlaneServiceClient", "HealthCheckCommand")
  .sc(HealthCheck$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: {};
      output: HealthCheckOutput;
    };
    sdk: {
      input: HealthCheckCommandInput;
      output: HealthCheckCommandOutput;
    };
  };
}
