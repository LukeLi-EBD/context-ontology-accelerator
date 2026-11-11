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
import type { GetSourceTableInput, GetSourceTableOutput } from "../models/models_1";
import { GetSourceTable$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetSourceTableCommand}.
 */
export interface GetSourceTableCommandInput extends GetSourceTableInput {}
/**
 * @public
 *
 * The output of {@link GetSourceTableCommand}.
 */
export interface GetSourceTableCommandOutput extends GetSourceTableOutput, __MetadataBearer {}

/**
 * Get full table metadata including all columns with business metadata.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetSourceTableCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetSourceTableCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetSourceTableInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   tableId: "STRING_VALUE", // required
 * };
 * const command = new GetSourceTableCommand(input);
 * const response = await client.send(command);
 * // { // GetSourceTableOutput
 * //   tableId: "STRING_VALUE", // required
 * //   name: "STRING_VALUE", // required
 * //   database: "STRING_VALUE", // required
 * //   reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED", // required
 * //   columns: [ // ColumnMetadataList // required
 * //     { // ColumnMetadata
 * //       name: "STRING_VALUE", // required
 * //       dataType: "STRING_VALUE", // required
 * //       nullable: true || false,
 * //       isPartitionKey: true || false,
 * //       description: "STRING_VALUE",
 * //       businessMetadata: { // BusinessMetadataOutput
 * //         description: "STRING_VALUE",
 * //         synonyms: [ // StringList
 * //           "STRING_VALUE",
 * //         ],
 * //         glossaryTerms: [
 * //           "STRING_VALUE",
 * //         ],
 * //         tags: [
 * //           "STRING_VALUE",
 * //         ],
 * //         enrichmentSource: "STRING_VALUE",
 * //         reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED",
 * //         confidence: Number("float"),
 * //       },
 * //       distinctValues: [ // DistinctValueList
 * //         "STRING_VALUE",
 * //       ],
 * //       pendingDeletion: true || false,
 * //     },
 * //   ],
 * //   businessMetadata: {
 * //     description: "STRING_VALUE",
 * //     synonyms: [
 * //       "STRING_VALUE",
 * //     ],
 * //     glossaryTerms: [
 * //       "STRING_VALUE",
 * //     ],
 * //     tags: "<StringList>",
 * //     enrichmentSource: "STRING_VALUE",
 * //     reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED",
 * //     confidence: Number("float"),
 * //   },
 * //   primaryKey: { // PrimaryKeyOutput
 * //     columns: "<StringList>",
 * //     source: "STRING_VALUE",
 * //     confidence: Number("float"),
 * //   },
 * //   foreignKeys: [ // ForeignKeyList
 * //     { // ForeignKeyOutput
 * //       column: "STRING_VALUE",
 * //       targetTable: "STRING_VALUE",
 * //       targetColumn: "STRING_VALUE",
 * //       source: "STRING_VALUE",
 * //       confidence: Number("float"),
 * //       reviewStatus: "STRING_VALUE",
 * //       targetDatasourceId: "STRING_VALUE",
 * //       provenance: "STRING_VALUE",
 * //     },
 * //   ],
 * //   technicalMetadata: { // TechnicalMetadataOutput
 * //     columnCount: Number("int"),
 * //     partitionKeys: "<StringList>",
 * //     format: "STRING_VALUE",
 * //     location: "STRING_VALUE",
 * //   },
 * //   pendingDeletion: true || false,
 * //   rescanDiff: { // RescanTableDiff
 * //     tableFields: [ // RescanFieldChangeList
 * //       { // RescanFieldChange
 * //         field: "STRING_VALUE", // required
 * //         kind: "SCHEMA" || "DESCRIPTION" || "CONSTRAINT" || "SAMPLED_VALUES", // required
 * //         old: "STRING_VALUE",
 * //         new: "STRING_VALUE",
 * //       },
 * //     ],
 * //     columns: [ // RescanColumnChangeList
 * //       { // RescanColumnChange
 * //         name: "STRING_VALUE", // required
 * //         status: "added" || "removed" || "modified", // required
 * //         fields: [
 * //           {
 * //             field: "STRING_VALUE", // required
 * //             kind: "SCHEMA" || "DESCRIPTION" || "CONSTRAINT" || "SAMPLED_VALUES", // required
 * //             old: "STRING_VALUE",
 * //             new: "STRING_VALUE",
 * //           },
 * //         ],
 * //       },
 * //     ],
 * //   },
 * //   added: true || false,
 * // };
 *
 * ```
 *
 * @param GetSourceTableCommandInput - {@link GetSourceTableCommandInput}
 * @returns {@link GetSourceTableCommandOutput}
 * @see {@link GetSourceTableCommandInput} for command's `input` shape.
 * @see {@link GetSourceTableCommandOutput} for command's `response` shape.
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
 * @example Get full metadata for the orders table
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.orders"
 * };
 * const command = new GetSourceTableCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   businessMetadata: {
 *     confidence: 0.88,
 *     description: "Customer orders fact table",
 *     enrichmentSource: "AI_GENERATED",
 *     glossaryTerms: [
 *       "Order"
 *     ],
 *     reviewStatus: "PENDING_REVIEW",
 *     synonyms: [
 *       "sales orders"
 *     ],
 *     tags: [
 *       "sales"
 *     ]
 *   },
 *   columns: [
 *     {
 *       businessMetadata: {
 *         confidence: 0.92,
 *         description: "Primary key for an order",
 *         enrichmentSource: "AI_GENERATED",
 *         glossaryTerms: [
 *           "Order"
 *         ],
 *         reviewStatus: "PENDING_REVIEW",
 *         synonyms: [
 *           "order number"
 *         ],
 *         tags: [
 *           "pii-none"
 *         ]
 *       },
 *       dataType: "bigint",
 *       description: "Unique order identifier",
 *       distinctValues: [
 *         "1001",
 *         "1002",
 *         "1003"
 *       ],
 *       isPartitionKey: false,
 *       name: "order_id",
 *       nullable: false
 *     },
 *     {
 *       dataType: "varchar",
 *       distinctValues: [
 *         "PLACED",
 *         "SHIPPED",
 *         "DELIVERED"
 *       ],
 *       isPartitionKey: false,
 *       name: "status",
 *       nullable: false
 *     }
 *   ],
 *   database: "sales",
 *   foreignKeys: [
 *     {
 *       column: "customer_id",
 *       confidence: 0.81,
 *       source: "AI_INFERRED",
 *       targetColumn: "customer_id",
 *       targetTable: "sales.customers"
 *     }
 *   ],
 *   name: "orders",
 *   primaryKey: {
 *     columns: [
 *       "order_id"
 *     ],
 *     confidence: 1.0,
 *     source: "DISCOVERED"
 *   },
 *   reviewStatus: "PENDING_REVIEW",
 *   tableId: "sales.orders",
 *   technicalMetadata: {
 *     columnCount: 8,
 *     format: "PARQUET",
 *     location: "s3://example-bucket/sales/orders/",
 *     partitionKeys: [
 *       "order_date"
 *     ]
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetSourceTableCommand extends $Command
  .classBuilder<
    GetSourceTableCommandInput,
    GetSourceTableCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetSourceTable", {})
  .n("ControlPlaneServiceClient", "GetSourceTableCommand")
  .sc(GetSourceTable$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetSourceTableInput;
      output: GetSourceTableOutput;
    };
    sdk: {
      input: GetSourceTableCommandInput;
      output: GetSourceTableCommandOutput;
    };
  };
}
