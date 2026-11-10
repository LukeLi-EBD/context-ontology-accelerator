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
import type { GetMetricReportManifestInput, GetMetricReportManifestOutput } from "../models/models_0";
import { GetMetricReportManifest$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetMetricReportManifestCommand}.
 */
export interface GetMetricReportManifestCommandInput extends GetMetricReportManifestInput {}
/**
 * @public
 *
 * The output of {@link GetMetricReportManifestCommand}.
 */
export interface GetMetricReportManifestCommandOutput extends GetMetricReportManifestOutput, __MetadataBearer {}

/**
 * Read the governed metrics report manifest. Every row carries its external
 * status, execution path and computability, all read from
 * platform.metric_definition; nothing is computed or invented here.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetMetricReportManifestCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetMetricReportManifestCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetMetricReportManifestInput
 *   namespaceId: "STRING_VALUE", // required
 *   scope: "STRING_VALUE",
 *   domain: "STRING_VALUE",
 *   evidenceBasis: "STRING_VALUE",
 *   publishable: true || false,
 * };
 * const command = new GetMetricReportManifestCommand(input);
 * const response = await client.send(command);
 * // { // GetMetricReportManifestOutput
 * //   items: [ // MetricReportItemList // required
 * //     { // MetricReportItem
 * //       metricId: "STRING_VALUE", // required
 * //       nameZh: "STRING_VALUE",
 * //       displayName: "STRING_VALUE",
 * //       domain: "STRING_VALUE",
 * //       publishable: true || false,
 * //       evidenceBasis: "STRING_VALUE",
 * //       evidenceBasisLabel: "STRING_VALUE",
 * //       evidenceSource: "STRING_VALUE",
 * //       hasRegulatoryText: true || false,
 * //       industryBaseline: true || false,
 * //       internalNotice: "STRING_VALUE",
 * //       e1Baseline: true || false,
 * //       formula: "STRING_VALUE",
 * //       formulaExpr: "STRING_VALUE",
 * //       computability: "STRING_VALUE",
 * //       computabilityLabel: "STRING_VALUE",
 * //       computabilityTone: "STRING_VALUE",
 * //       gap: "STRING_VALUE",
 * //       gapCode: "STRING_VALUE",
 * //       missing: "STRING_VALUE",
 * //       externalEligible: true || false,
 * //       externalStatus: "STRING_VALUE",
 * //       externalLabel: "STRING_VALUE",
 * //       externalReason: "STRING_VALUE",
 * //       executionPath: "STRING_VALUE",
 * //       executable: true || false,
 * //       executionReason: "STRING_VALUE",
 * //       executionReasonCode: "STRING_VALUE",
 * //       observationCount: Number("int"),
 * //       availableWindowDays: Number("int"),
 * //       minWindowDays: Number("int"),
 * //       windowSufficient: true || false,
 * //       windowWarning: "STRING_VALUE",
 * //       variantOf: "STRING_VALUE",
 * //       outputMode: "STRING_VALUE",
 * //       formulaDisabled: true || false,
 * //       inference: true || false,
 * //       evidenceStatus: "STRING_VALUE",
 * //       definitionVersion: "STRING_VALUE",
 * //     },
 * //   ],
 * //   count: Number("int"), // required
 * //   meta: { // MetricReportMeta
 * //     generatedAt: "STRING_VALUE", // required
 * //     source: "STRING_VALUE",
 * //     scope: "STRING_VALUE",
 * //     total: Number("int"),
 * //     allTotal: Number("int"),
 * //     counts: { // MetricReportCounts
 * //       publishableTrue: Number("int"),
 * //       industry: Number("int"),
 * //       regulatory: Number("int"),
 * //       externalEligible: Number("int"),
 * //       externalCandidates: Number("int"),
 * //       executableNow: Number("int"),
 * //       industryExcludedFromExternal: Number("int"),
 * //       computability: { // MetricReportComputabilityCounts
 * //         "<keys>": Number("int"),
 * //       },
 * //     },
 * //     execution: { // MetricReportExecution
 * //       externalCandidates: Number("int"),
 * //       executableNow: Number("int"),
 * //       ruleSetOnly: Number("int"),
 * //       unavailable: Number("int"),
 * //       byReason: { // MetricReportExecutionReasons
 * //         "<keys>": Number("int"),
 * //       },
 * //       basis: "STRING_VALUE",
 * //       note: "STRING_VALUE",
 * //     },
 * //     industryNotice: "STRING_VALUE",
 * //     externalScopeRule: "STRING_VALUE",
 * //     disclaimer: "STRING_VALUE",
 * //   },
 * //   filters: { // MetricReportFilters
 * //     scope: "STRING_VALUE",
 * //     domain: "STRING_VALUE",
 * //     evidenceBasis: "STRING_VALUE",
 * //     publishable: true || false,
 * //   },
 * // };
 *
 * ```
 *
 * @param GetMetricReportManifestCommandInput - {@link GetMetricReportManifestCommandInput}
 * @returns {@link GetMetricReportManifestCommandOutput}
 * @see {@link GetMetricReportManifestCommandInput} for command's `input` shape.
 * @see {@link GetMetricReportManifestCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
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
 * @example One manifest row
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd",
 *   scope: "all"
 * };
 * const command = new GetMetricReportManifestCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   count: 1,
 *   filters: {
 *     scope: "all"
 *   },
 *   items: [
 *     {
 *       availableWindowDays: 0,
 *       computability: "structurally_computable",
 *       computabilityLabel: "结构性可算（需事实与观测）",
 *       computabilityTone: "ok",
 *       definitionVersion: "v3",
 *       domain: "insurance",
 *       e1Baseline: false,
 *       evidenceBasis: "regulatory",
 *       evidenceBasisLabel: "监管原文",
 *       evidenceSource: "监管原文",
 *       evidenceStatus: "regulatory_verified",
 *       executable: false,
 *       executionPath: "unavailable",
 *       executionReason: "该口径是族索引，需先选择变体",
 *       executionReasonCode: "variant_required",
 *       externalEligible: true,
 *       externalLabel: "对外可出数候选（需事实与观测）",
 *       externalReason: "证据为监管原文、publishable=true、口径结构性可算；资格判定未含观测与窗口，实际可执行性见 executionPath",
 *       externalStatus: "external_candidate",
 *       formula: "口径未给出",
 *       formulaDisabled: false,
 *       gap: "族索引：需指定变体（E_METRIC_VARIANT_REQUIRED）",
 *       gapCode: "variant_required",
 *       hasRegulatoryText: true,
 *       industryBaseline: false,
 *       inference: false,
 *       metricId: "FIN-INS-022",
 *       minWindowDays: 390,
 *       nameZh: "13 个月保费继续率",
 *       observationCount: 0,
 *       outputMode: "index",
 *       publishable: true,
 *       windowSufficient: false
 *     }
 *   ],
 *   meta: {
 *     allTotal: 85,
 *     counts: {
 *       computability: {
 *         blocked_semantics: 25,
 *         structurally_computable: 60
 *       },
 *       executableNow: 0,
 *       externalCandidates: 35,
 *       externalEligible: 35,
 *       industry: 25,
 *       industryExcludedFromExternal: 0,
 *       publishableTrue: 60,
 *       regulatory: 60
 *     },
 *     disclaimer: "可算性仅表示口径四元组与公式可编译，不代表已有观测值；本清单不承诺业务数值。",
 *     externalScopeRule: "evidence_basis=regulatory 且 publishable=true 且 computability_tier=structurally_computable",
 *     generatedAt: "2026-11-10T12:00:00+00:00",
 *     scope: "all",
 *     source: "platform.metric_definition",
 *     total: 85
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetMetricReportManifestCommand extends $Command
  .classBuilder<
    GetMetricReportManifestCommandInput,
    GetMetricReportManifestCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetMetricReportManifest", {})
  .n("ControlPlaneServiceClient", "GetMetricReportManifestCommand")
  .sc(GetMetricReportManifest$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetMetricReportManifestInput;
      output: GetMetricReportManifestOutput;
    };
    sdk: {
      input: GetMetricReportManifestCommandInput;
      output: GetMetricReportManifestCommandOutput;
    };
  };
}
