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
import type { GetSourceScanJobInput, GetSourceScanJobOutput } from "../models/models_0";
import { GetSourceScanJob$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetSourceScanJobCommand}.
 */
export interface GetSourceScanJobCommandInput extends GetSourceScanJobInput {}
/**
 * @public
 *
 * The output of {@link GetSourceScanJobCommand}.
 */
export interface GetSourceScanJobCommandOutput extends GetSourceScanJobOutput, __MetadataBearer {}

/**
 * Get the status and results of a scan job for a DATABASE source.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetSourceScanJobCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetSourceScanJobCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetSourceScanJobInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 * };
 * const command = new GetSourceScanJobCommand(input);
 * const response = await client.send(command);
 * // { // GetSourceScanJobOutput
 * //   jobId: "STRING_VALUE", // required
 * //   sourceId: "STRING_VALUE", // required
 * //   status: "IN_PROGRESS" || "DISCOVERING" || "ENRICHING" || "COMPLETED" || "FAILED" || "CANCELLED", // required
 * //   tablesDiscovered: Number("int"),
 * //   tablesProcessed: Number("int"),
 * //   tablesTotal: Number("int"),
 * //   tablesAdded: Number("int"),
 * //   tablesRemoved: Number("int"),
 * //   tablesModified: Number("int"),
 * //   startedAt: new Date("TIMESTAMP"), // required
 * //   completedAt: new Date("TIMESTAMP"),
 * //   errorMessage: "STRING_VALUE",
 * //   tablesFailed: Number("int"),
 * //   failedTables: [ // FailedTableList
 * //     "STRING_VALUE",
 * //   ],
 * //   filterWarnings: [ // FilterWarningList
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param GetSourceScanJobCommandInput - {@link GetSourceScanJobCommandInput}
 * @returns {@link GetSourceScanJobCommandOutput}
 * @see {@link GetSourceScanJobCommandInput} for command's `input` shape.
 * @see {@link GetSourceScanJobCommandOutput} for command's `response` shape.
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
 * @example Get the status of a completed scan job
 * ```javascript
 * //
 * const input = {
 *   jobId: "job-8b21d4f0",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new GetSourceScanJobCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   completedAt: "2026-07-23T14:35:00Z",
 *   jobId: "job-8b21d4f0",
 *   sourceId: "src-7f3a9c1e",
 *   startedAt: "2026-07-23T14:30:00Z",
 *   status: "COMPLETED",
 *   tablesAdded: 2,
 *   tablesDiscovered: 12,
 *   tablesModified: 1,
 *   tablesRemoved: 0
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetSourceScanJobCommand extends $Command
  .classBuilder<
    GetSourceScanJobCommandInput,
    GetSourceScanJobCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetSourceScanJob", {})
  .n("ControlPlaneServiceClient", "GetSourceScanJobCommand")
  .sc(GetSourceScanJob$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetSourceScanJobInput;
      output: GetSourceScanJobOutput;
    };
    sdk: {
      input: GetSourceScanJobCommandInput;
      output: GetSourceScanJobCommandOutput;
    };
  };
}
