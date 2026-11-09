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
import type { BulkDeleteMetricsInput, BulkDeleteMetricsOutput } from "../models/models_0";
import { BulkDeleteMetrics$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link BulkDeleteMetricsCommand}.
 */
export interface BulkDeleteMetricsCommandInput extends BulkDeleteMetricsInput {}
/**
 * @public
 *
 * The output of {@link BulkDeleteMetricsCommand}.
 */
export interface BulkDeleteMetricsCommandOutput extends BulkDeleteMetricsOutput, __MetadataBearer {}

/**
 * Delete multiple metrics by name list or filter criteria.
 * Returns the count of metrics deleted.
 *
 * Takes no `clientToken`: deletion is naturally idempotent. A retry deletes
 * nothing further; metrics already removed are reported in `notFound` (names)
 * or are simply no longer matched (filter / deleteAll).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, BulkDeleteMetricsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, BulkDeleteMetricsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // BulkDeleteMetricsInput
 *   namespaceId: "STRING_VALUE", // required
 *   names: [ // MetricNameList
 *     "STRING_VALUE",
 *   ],
 *   filter: { // BulkDeleteFilter
 *     dataSourceId: "STRING_VALUE",
 *     sourceTable: "STRING_VALUE",
 *     namePrefix: "STRING_VALUE",
 *   },
 *   deleteAll: true || false,
 * };
 * const command = new BulkDeleteMetricsCommand(input);
 * const response = await client.send(command);
 * // { // BulkDeleteMetricsOutput
 * //   deleted: Number("int"), // required
 * //   notFound: [ // MetricNameList
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param BulkDeleteMetricsCommandInput - {@link BulkDeleteMetricsCommandInput}
 * @returns {@link BulkDeleteMetricsCommandOutput}
 * @see {@link BulkDeleteMetricsCommandInput} for command's `input` shape.
 * @see {@link BulkDeleteMetricsCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
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
 * @example Delete metrics by name
 * ```javascript
 * //
 * const input = {
 *   names: [
 *     "total_revenue",
 *     "avg_order_value",
 *     "legacy_metric"
 *   ],
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new BulkDeleteMetricsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   deleted: 2,
 *   notFound: [
 *     "legacy_metric"
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class BulkDeleteMetricsCommand extends $Command
  .classBuilder<
    BulkDeleteMetricsCommandInput,
    BulkDeleteMetricsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "BulkDeleteMetrics", {})
  .n("ControlPlaneServiceClient", "BulkDeleteMetricsCommand")
  .sc(BulkDeleteMetrics$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: BulkDeleteMetricsInput;
      output: BulkDeleteMetricsOutput;
    };
    sdk: {
      input: BulkDeleteMetricsCommandInput;
      output: BulkDeleteMetricsCommandOutput;
    };
  };
}
