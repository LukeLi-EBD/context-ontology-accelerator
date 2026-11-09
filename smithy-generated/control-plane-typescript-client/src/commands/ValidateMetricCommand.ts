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
import type { ValidateMetricInput, ValidateMetricOutput } from "../models/models_0";
import { ValidateMetric$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ValidateMetricCommand}.
 */
export interface ValidateMetricCommandInput extends ValidateMetricInput {}
/**
 * @public
 *
 * The output of {@link ValidateMetricCommand}.
 */
export interface ValidateMetricCommandOutput extends ValidateMetricOutput, __MetadataBearer {}

/**
 * Validate a metric definition without persisting it. ERROR findings predict
 * create/update rejection; INFO findings are advisory.
 *
 * Takes no `clientToken`: nothing is persisted, so a retry simply validates again.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ValidateMetricCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ValidateMetricCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ValidateMetricInput
 *   namespaceId: "STRING_VALUE", // required
 *   name: "STRING_VALUE", // required
 *   label: "STRING_VALUE",
 *   description: "STRING_VALUE", // required
 *   expression: { // MetricExpression
 *     dialects: [ // MetricDialectList // required
 *       { // MetricDialect
 *         dialect: "POSTGRESQL" || "TRINO" || "REDSHIFT" || "SNOWFLAKE" || "DATABRICKS" || "MYSQL", // required
 *         expression: "STRING_VALUE", // required
 *       },
 *     ],
 *   },
 *   dataSourceId: "STRING_VALUE", // required
 *   sourceTable: "STRING_VALUE", // required
 *   defaultTimeGrain: "DAY" || "WEEK" || "MONTH" || "QUARTER" || "YEAR",
 *   unit: "STRING_VALUE",
 *   returnType: "STRING_VALUE",
 *   aiContext: { // MetricAiContext
 *     synonyms: [ // SynonymList
 *       "STRING_VALUE",
 *     ],
 *     instructions: "STRING_VALUE",
 *     examples: [ // ExampleList
 *       "STRING_VALUE",
 *     ],
 *   },
 *   ontologyConcepts: [ // OntologyConceptList
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new ValidateMetricCommand(input);
 * const response = await client.send(command);
 * // { // ValidateMetricOutput
 * //   warnings: [ // ValidationWarningList // required
 * //     { // ValidationWarning
 * //       field: "STRING_VALUE", // required
 * //       message: "STRING_VALUE", // required
 * //       severity: "ERROR" || "WARNING" || "INFO", // required
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ValidateMetricCommandInput - {@link ValidateMetricCommandInput}
 * @returns {@link ValidateMetricCommandOutput}
 * @see {@link ValidateMetricCommandInput} for command's `input` shape.
 * @see {@link ValidateMetricCommandOutput} for command's `response` shape.
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
 * @example Validate a metric definition
 * ```javascript
 * //
 * const input = {
 *   dataSourceId: "warehouse-pg-01",
 *   defaultTimeGrain: "DAY",
 *   description: "Average net revenue per order.",
 *   expression: {
 *     dialects: [
 *       {
 *         dialect: "POSTGRESQL",
 *         expression: "SELECT AVG(net_amount) FROM public.orders"
 *       }
 *     ]
 *   },
 *   name: "avg_order_value",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   returnType: "decimal",
 *   sourceTable: "public.orders",
 *   unit: "USD"
 * };
 * const command = new ValidateMetricCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   warnings: [
 *     {
 *       field: "unit",
 *       message: "Unit 'USD' is not recognized by the currency registry; using as free-text.",
 *       severity: "INFO"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ValidateMetricCommand extends $Command
  .classBuilder<
    ValidateMetricCommandInput,
    ValidateMetricCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ValidateMetric", {})
  .n("ControlPlaneServiceClient", "ValidateMetricCommand")
  .sc(ValidateMetric$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ValidateMetricInput;
      output: ValidateMetricOutput;
    };
    sdk: {
      input: ValidateMetricCommandInput;
      output: ValidateMetricCommandOutput;
    };
  };
}
