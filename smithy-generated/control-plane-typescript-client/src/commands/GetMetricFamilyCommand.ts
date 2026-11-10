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
import type { GetMetricFamilyInput, GetMetricFamilyOutput } from "../models/models_0";
import { GetMetricFamily$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetMetricFamilyCommand}.
 */
export interface GetMetricFamilyCommandInput extends GetMetricFamilyInput {}
/**
 * @public
 *
 * The output of {@link GetMetricFamilyCommand}.
 */
export interface GetMetricFamilyCommandOutput extends GetMetricFamilyOutput, __MetadataBearer {}

/**
 * Read one metric family: the index metric and its variants side by side.
 * The family index never yields a value; callers must pick a variant and use
 * the variant's metricId for output.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetMetricFamilyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetMetricFamilyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetMetricFamilyInput
 *   namespaceId: "STRING_VALUE", // required
 *   familyId: "STRING_VALUE", // required
 * };
 * const command = new GetMetricFamilyCommand(input);
 * const response = await client.send(command);
 * // { // GetMetricFamilyOutput
 * //   family: { // MetricFamily
 * //     familyId: "STRING_VALUE", // required
 * //     indexMetricId: "STRING_VALUE", // required
 * //     nameZh: "STRING_VALUE",
 * //     selectionRequired: true || false, // required
 * //     guidance: { // MetricFamilyGuidance
 * //       code: "STRING_VALUE", // required
 * //       message: "STRING_VALUE", // required
 * //       howTo: [ // MetricFamilyHowToList // required
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //     variantCount: Number("int"), // required
 * //     variants: [ // MetricFamilyVariantList // required
 * //       { // MetricFamilyVariant
 * //         metricId: "STRING_VALUE", // required
 * //         nameZh: "STRING_VALUE",
 * //         displayName: "STRING_VALUE",
 * //         publishable: true || false,
 * //         evidenceBasis: "STRING_VALUE",
 * //         externalEligible: true || false,
 * //         internalNotice: "STRING_VALUE",
 * //         formula: "STRING_VALUE",
 * //         formulaDisabled: true || false,
 * //         computability: "STRING_VALUE",
 * //         computabilityLabel: "STRING_VALUE",
 * //         window: { // MetricFamilyVariantWindow
 * //           kind: "STRING_VALUE",
 * //           minWindowDays: Number("int"),
 * //           text: "STRING_VALUE",
 * //         },
 * //         denominator: "STRING_VALUE",
 * //         denominatorText: "STRING_VALUE",
 * //         grain: "STRING_VALUE",
 * //         grainCode: "STRING_VALUE",
 * //         metricKind: "STRING_VALUE",
 * //         unit: "STRING_VALUE",
 * //       },
 * //     ],
 * //     diffs: [ // MetricFamilyDiffList // required
 * //       { // MetricFamilyDiff
 * //         field: "STRING_VALUE", // required
 * //         label: "STRING_VALUE", // required
 * //         values: { // MetricFamilyDiffValues // required
 * //           "<keys>": "STRING_VALUE",
 * //         },
 * //         different: true || false, // required
 * //       },
 * //     ],
 * //     source: "STRING_VALUE", // required
 * //   },
 * // };
 *
 * ```
 *
 * @param GetMetricFamilyCommandInput - {@link GetMetricFamilyCommandInput}
 * @returns {@link GetMetricFamilyCommandOutput}
 * @see {@link GetMetricFamilyCommandInput} for command's `input` shape.
 * @see {@link GetMetricFamilyCommandOutput} for command's `response` shape.
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
 * @example Insurance continuation-rate family
 * ```javascript
 * //
 * const input = {
 *   familyId: "FIN-INS-022",
 *   namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd"
 * };
 * const command = new GetMetricFamilyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   family: {
 *     diffs: [
 *       {
 *         different: false,
 *         field: "observationPeriod",
 *         label: "观察窗口",
 *         values: {
 *           FIN-INS-022-v1: "13 个月（390 天）",
 *           FIN-INS-022-v2: "13 个月（390 天）"
 *         }
 *       }
 *     ],
 *     familyId: "FIN-INS-022",
 *     guidance: {
 *       code: "E_METRIC_VARIANT_REQUIRED",
 *       howTo: [
 *         "在族索引详情中选择一个变体（窗口/分母/粒度会并排展示）",
 *         "前端将变体 metric_id 回填到详情与 URL",
 *         "再用该 metric_id 调用 /metrics/{metric_id}/output"
 *       ],
 *       message: "该指标是口径族索引，不直接出数；请先选择变体并回填 metric_id。"
 *     },
 *     indexMetricId: "FIN-INS-022",
 *     nameZh: "13 个月保费继续率",
 *     selectionRequired: true,
 *     source: "platform.metric_definition",
 *     variantCount: 2,
 *     variants: [
 *       {
 *         computability: "structurally_computable",
 *         computabilityLabel: "结构性可算（需事实与观测）",
 *         evidenceBasis: "regulatory",
 *         externalEligible: true,
 *         formula: "13 个月继续率 = 期初后第 13 个月仍有效保单 / 期初保单",
 *         formulaDisabled: false,
 *         metricId: "FIN-INS-022-v1",
 *         nameZh: "13 个月保费继续率（宽限期口径）",
 *         publishable: true
 *       },
 *       {
 *         computability: "structurally_computable",
 *         computabilityLabel: "结构性可算（需事实与观测）",
 *         evidenceBasis: "regulatory",
 *         externalEligible: true,
 *         formula: "13 个月继续率 = 期初后第 13 个月仍有效保单 / 期初保单",
 *         formulaDisabled: false,
 *         metricId: "FIN-INS-022-v2",
 *         nameZh: "13 个月保费继续率（自然月口径）",
 *         publishable: true
 *       }
 *     ]
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetMetricFamilyCommand extends $Command
  .classBuilder<
    GetMetricFamilyCommandInput,
    GetMetricFamilyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetMetricFamily", {})
  .n("ControlPlaneServiceClient", "GetMetricFamilyCommand")
  .sc(GetMetricFamily$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetMetricFamilyInput;
      output: GetMetricFamilyOutput;
    };
    sdk: {
      input: GetMetricFamilyCommandInput;
      output: GetMetricFamilyCommandOutput;
    };
  };
}
