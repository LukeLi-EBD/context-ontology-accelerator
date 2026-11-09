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
import type { UpdateSourceTableKeysInput, UpdateSourceTableKeysOutput } from "../models/models_0";
import { UpdateSourceTableKeys$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateSourceTableKeysCommand}.
 */
export interface UpdateSourceTableKeysCommandInput extends UpdateSourceTableKeysInput {}
/**
 * @public
 *
 * The output of {@link UpdateSourceTableKeysCommand}.
 */
export interface UpdateSourceTableKeysCommandOutput extends UpdateSourceTableKeysOutput, __MetadataBearer {}

/**
 * Edit a table's primary key and foreign key relationships. Steward intent is
 * authoritative: affected keys are stored with source = STEWARD_SPECIFIED,
 * overriding deterministic or AI-inferred keys. Provide `primaryKey` and/or
 * `foreignKeys` — an omitted field is left unchanged; an empty list clears it.
 * Key columns are validated against the table's columns. Does NOT change
 * reviewStatus.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UpdateSourceTableKeysCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UpdateSourceTableKeysCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UpdateSourceTableKeysInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   tableId: "STRING_VALUE", // required
 *   primaryKey: { // PrimaryKeyInput
 *     columns: [ // PrimaryKeyColumnList // required
 *       "STRING_VALUE",
 *     ],
 *   },
 *   foreignKeys: [ // ForeignKeyInputList
 *     { // ForeignKeyInput
 *       column: "STRING_VALUE", // required
 *       targetTable: "STRING_VALUE", // required
 *       targetColumn: "STRING_VALUE",
 *       source: "STRING_VALUE",
 *       reviewStatus: "STRING_VALUE",
 *       targetDatasourceId: "STRING_VALUE",
 *       provenance: "STRING_VALUE",
 *     },
 *   ],
 * };
 * const command = new UpdateSourceTableKeysCommand(input);
 * const response = await client.send(command);
 * // { // UpdateSourceTableKeysOutput
 * //   tableId: "STRING_VALUE", // required
 * //   reviewStatus: "PENDING_REVIEW" || "APPROVED" || "REJECTED", // required
 * // };
 *
 * ```
 *
 * @param UpdateSourceTableKeysCommandInput - {@link UpdateSourceTableKeysCommandInput}
 * @returns {@link UpdateSourceTableKeysCommandOutput}
 * @see {@link UpdateSourceTableKeysCommandInput} for command's `input` shape.
 * @see {@link UpdateSourceTableKeysCommandOutput} for command's `response` shape.
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
 * @example Set the primary key and a foreign key on a table
 * ```javascript
 * //
 * const input = {
 *   foreignKeys: [
 *     {
 *       column: "customer_id",
 *       targetColumn: "customer_id",
 *       targetTable: "sales.customers"
 *     }
 *   ],
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   primaryKey: {
 *     columns: [
 *       "order_id"
 *     ]
 *   },
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.orders"
 * };
 * const command = new UpdateSourceTableKeysCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   reviewStatus: "PENDING_REVIEW",
 *   tableId: "sales.orders"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UpdateSourceTableKeysCommand extends $Command
  .classBuilder<
    UpdateSourceTableKeysCommandInput,
    UpdateSourceTableKeysCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UpdateSourceTableKeys", {})
  .n("ControlPlaneServiceClient", "UpdateSourceTableKeysCommand")
  .sc(UpdateSourceTableKeys$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UpdateSourceTableKeysInput;
      output: UpdateSourceTableKeysOutput;
    };
    sdk: {
      input: UpdateSourceTableKeysCommandInput;
      output: UpdateSourceTableKeysCommandOutput;
    };
  };
}
