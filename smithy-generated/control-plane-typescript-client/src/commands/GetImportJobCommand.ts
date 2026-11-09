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
import type { GetImportJobInput, ImportJobOutput } from "../models/models_0";
import { GetImportJob$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetImportJobCommand}.
 */
export interface GetImportJobCommandInput extends GetImportJobInput {}
/**
 * @public
 *
 * The output of {@link GetImportJobCommand}.
 */
export interface GetImportJobCommandOutput extends ImportJobOutput, __MetadataBearer {}

/**
 * Poll the status of an asynchronous OSI import job.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetImportJobCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetImportJobCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetImportJobInput
 *   namespaceId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 * };
 * const command = new GetImportJobCommand(input);
 * const response = await client.send(command);
 * // { // ImportJobOutput
 * //   jobId: "STRING_VALUE", // required
 * //   status: "STRING_VALUE", // required
 * //   metricsTotal: Number("int"), // required
 * //   metricsProcessed: Number("int"), // required
 * //   metricsCreated: Number("int"), // required
 * //   metricsUpdated: Number("int"), // required
 * //   errors: [ // OsiWarningList
 * //     "STRING_VALUE",
 * //   ],
 * //   warnings: [
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param GetImportJobCommandInput - {@link GetImportJobCommandInput}
 * @returns {@link GetImportJobCommandOutput}
 * @see {@link GetImportJobCommandInput} for command's `input` shape.
 * @see {@link GetImportJobCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
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
 * @example Poll an in-progress import job
 * ```javascript
 * //
 * const input = {
 *   jobId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetImportJobCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   errors:   [],
 *   jobId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *   metricsCreated: 300,
 *   metricsProcessed: 320,
 *   metricsTotal: 500,
 *   metricsUpdated: 20,
 *   status: "IN_PROGRESS",
 *   warnings: [
 *     "Metric 'legacy_gmv' skipped: no matching data source."
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetImportJobCommand extends $Command
  .classBuilder<
    GetImportJobCommandInput,
    GetImportJobCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetImportJob", {})
  .n("ControlPlaneServiceClient", "GetImportJobCommand")
  .sc(GetImportJob$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetImportJobInput;
      output: ImportJobOutput;
    };
    sdk: {
      input: GetImportJobCommandInput;
      output: GetImportJobCommandOutput;
    };
  };
}
