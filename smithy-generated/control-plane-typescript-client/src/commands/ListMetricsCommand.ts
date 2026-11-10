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
import type { ListMetricsInput, ListMetricsOutput } from "../models/models_0";
import { ListMetrics$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListMetricsCommand}.
 */
export interface ListMetricsCommandInput extends ListMetricsInput {}
/**
 * @public
 *
 * The output of {@link ListMetricsCommand}.
 */
export interface ListMetricsCommandOutput extends ListMetricsOutput, __MetadataBearer {}

/**
 * List metric definitions in a namespace, optionally filtered by data source or source table.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListMetricsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListMetricsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListMetricsInput
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 *   namespaceId: "STRING_VALUE", // required
 *   dataSourceId: "STRING_VALUE",
 *   sourceTable: "STRING_VALUE",
 * };
 * const command = new ListMetricsCommand(input);
 * const response = await client.send(command);
 * // { // ListMetricsOutput
 * //   nextToken: "STRING_VALUE",
 * //   metrics: [ // MetricDefinitionList // required
 * //     { // MetricDefinition
 * //       metricId: "STRING_VALUE",
 * //       namespaceId: "STRING_VALUE",
 * //       name: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       description: "STRING_VALUE", // required
 * //       expression: { // MetricExpression
 * //         dialects: [ // MetricDialectList // required
 * //           { // MetricDialect
 * //             dialect: "POSTGRESQL" || "TRINO" || "REDSHIFT" || "SNOWFLAKE" || "DATABRICKS" || "MYSQL", // required
 * //             expression: "STRING_VALUE", // required
 * //           },
 * //         ],
 * //       },
 * //       dataSourceId: "STRING_VALUE", // required
 * //       sourceTable: "STRING_VALUE", // required
 * //       defaultTimeGrain: "DAY" || "WEEK" || "MONTH" || "QUARTER" || "YEAR",
 * //       unit: "STRING_VALUE",
 * //       returnType: "STRING_VALUE",
 * //       aiContext: { // MetricAiContext
 * //         synonyms: [ // SynonymList
 * //           "STRING_VALUE",
 * //         ],
 * //         instructions: "STRING_VALUE",
 * //         examples: [ // ExampleList
 * //           "STRING_VALUE",
 * //         ],
 * //       },
 * //       ontologyConcepts: [ // OntologyConceptList
 * //         "STRING_VALUE",
 * //       ],
 * //       definedBy: "STRING_VALUE",
 * //       effectiveFrom: "STRING_VALUE",
 * //       domain: "STRING_VALUE",
 * //       evidenceBasis: "STRING_VALUE",
 * //       publishable: true || false,
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListMetricsCommandInput - {@link ListMetricsCommandInput}
 * @returns {@link ListMetricsCommandOutput}
 * @see {@link ListMetricsCommandInput} for command's `input` shape.
 * @see {@link ListMetricsCommandOutput} for command's `response` shape.
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
 * @example List metrics filtered by source table
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   sourceTable: "public.orders"
 * };
 * const command = new ListMetricsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   metrics: [
 *     {
 *       dataSourceId: "warehouse-pg-01",
 *       defaultTimeGrain: "MONTH",
 *       description: "Sum of net revenue across all closed orders.",
 *       expression: {
 *         dialects: [
 *           {
 *             dialect: "POSTGRESQL",
 *             expression: "SELECT SUM(net_amount) FROM public.orders"
 *           }
 *         ]
 *       },
 *       metricId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *       name: "total_revenue",
 *       namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *       returnType: "decimal",
 *       sourceTable: "public.orders",
 *       unit: "USD"
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOjIwfQ"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListMetricsCommand extends $Command
  .classBuilder<
    ListMetricsCommandInput,
    ListMetricsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListMetrics", {})
  .n("ControlPlaneServiceClient", "ListMetricsCommand")
  .sc(ListMetrics$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListMetricsInput;
      output: ListMetricsOutput;
    };
    sdk: {
      input: ListMetricsCommandInput;
      output: ListMetricsCommandOutput;
    };
  };
}
