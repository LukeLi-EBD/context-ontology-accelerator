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
import type { GetMetricCardInput, MetricCard } from "../models/models_1";
import { GetMetricCard$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetMetricCardCommand}.
 */
export interface GetMetricCardCommandInput extends GetMetricCardInput {}
/**
 * @public
 *
 * The output of {@link GetMetricCardCommand}.
 */
export interface GetMetricCardCommandOutput extends MetricCard, __MetadataBearer {}

/**
 * Read the platform metric card.
 *
 * `bindingStatus` is first-class: an unbound metric reports `unbound` and an
 * empty `fieldBindings` list. The source table is never invented to hide it.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetMetricCardCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetMetricCardCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetMetricCardInput
 *   metricId: "STRING_VALUE", // required
 * };
 * const command = new GetMetricCardCommand(input);
 * const response = await client.send(command);
 * // { // MetricCard
 * //   metricId: "STRING_VALUE", // required
 * //   name: "STRING_VALUE",
 * //   domain: "STRING_VALUE",
 * //   evidenceBasis: "STRING_VALUE",
 * //   publishable: true || false,
 * //   inference: true || false,
 * //   formulaDisabled: true || false,
 * //   missing: "STRING_VALUE",
 * //   evidenceStatus: "STRING_VALUE",
 * //   note: "STRING_VALUE",
 * //   effectiveDate: "STRING_VALUE",
 * //   variantOf: "STRING_VALUE",
 * //   outputMode: "STRING_VALUE",
 * //   ruleSet: "DOCUMENT_VALUE",
 * //   definition: "STRING_VALUE",
 * //   formulaText: "STRING_VALUE",
 * //   denominatorText: "STRING_VALUE",
 * //   observationPeriodText: "STRING_VALUE",
 * //   granularityText: "STRING_VALUE",
 * //   grain: "STRING_VALUE",
 * //   provenanceLabel: "STRING_VALUE",
 * //   unit: "STRING_VALUE",
 * //   definitionVersion: "STRING_VALUE",
 * //   bindingStatus: "STRING_VALUE", // required
 * //   fieldBindings: [ // MetricFieldBindingList // required
 * //     { // MetricFieldBinding
 * //       role: "STRING_VALUE",
 * //       factTable: "STRING_VALUE",
 * //       entityColumn: "STRING_VALUE",
 * //       valueExpr: "STRING_VALUE",
 * //       agg: "STRING_VALUE",
 * //       filterSql: "STRING_VALUE",
 * //       windowColumn: "STRING_VALUE",
 * //       windowMode: "STRING_VALUE",
 * //     },
 * //   ],
 * //   externalEligible: true || false,
 * //   externalStatus: "STRING_VALUE",
 * //   externalLabel: "STRING_VALUE",
 * //   externalReason: "STRING_VALUE",
 * //   familyId: "STRING_VALUE",
 * //   variantMetricIds: [ // StringList // required
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param GetMetricCardCommandInput - {@link GetMetricCardCommandInput}
 * @returns {@link GetMetricCardCommandOutput}
 * @see {@link GetMetricCardCommandInput} for command's `input` shape.
 * @see {@link GetMetricCardCommandOutput} for command's `response` shape.
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
 * @example Read one metric card
 * ```javascript
 * //
 * const input = {
 *   metricId: "M-001"
 * };
 * const command = new GetMetricCardCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   bindingStatus: "bound",
 *   definitionVersion: "v3",
 *   domain: "contract",
 *   effectiveDate: "2026-01-01",
 *   evidenceBasis: "system",
 *   evidenceStatus: "complete",
 *   externalEligible: true,
 *   externalLabel: "可对外",
 *   externalReason: "证据链完整",
 *   externalStatus: "external_candidate",
 *   fieldBindings: [
 *     {
 *       agg: "sum",
 *       entityColumn: "contract_id",
 *       factTable: "fact_contract",
 *       role: "numerator",
 *       valueExpr: "amount",
 *       windowMode: "calendar"
 *     }
 *   ],
 *   formulaDisabled: false,
 *   grain: "contract",
 *   inference: false,
 *   metricId: "M-001",
 *   missing: "",
 *   name: "合同金额",
 *   note: "",
 *   outputMode: "single",
 *   publishable: true,
 *   variantMetricIds:   []
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetMetricCardCommand extends $Command
  .classBuilder<
    GetMetricCardCommandInput,
    GetMetricCardCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetMetricCard", {})
  .n("ControlPlaneServiceClient", "GetMetricCardCommand")
  .sc(GetMetricCard$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetMetricCardInput;
      output: MetricCard;
    };
    sdk: {
      input: GetMetricCardCommandInput;
      output: GetMetricCardCommandOutput;
    };
  };
}
