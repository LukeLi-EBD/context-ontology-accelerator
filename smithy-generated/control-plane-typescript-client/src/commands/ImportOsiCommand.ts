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
import type { ImportOsiInput, ImportOsiOutput } from "../models/models_0";
import { ImportOsi$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ImportOsiCommand}.
 */
export interface ImportOsiCommandInput extends ImportOsiInput {}
/**
 * @public
 *
 * The output of {@link ImportOsiCommand}.
 */
export interface ImportOsiCommandOutput extends ImportOsiOutput, __MetadataBearer {}

/**
 * Import metrics from an OSI (Open Semantic Interchange) YAML document, inline or from S3.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ImportOsiCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ImportOsiCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ImportOsiInput
 *   namespaceId: "STRING_VALUE", // required
 *   content: "STRING_VALUE",
 *   s3Key: "STRING_VALUE",
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new ImportOsiCommand(input);
 * const response = await client.send(command);
 * // { // ImportOsiOutput
 * //   datasetsResolved: Number("int"), // required
 * //   metricsCreated: Number("int"), // required
 * //   metricsUpdated: Number("int"), // required
 * //   warnings: [ // OsiWarningList
 * //     "STRING_VALUE",
 * //   ],
 * //   jobId: "STRING_VALUE",
 * //   status: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ImportOsiCommandInput - {@link ImportOsiCommandInput}
 * @returns {@link ImportOsiCommandOutput}
 * @see {@link ImportOsiCommandInput} for command's `input` shape.
 * @see {@link ImportOsiCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Import metrics from inline OSI YAML
 * ```javascript
 * //
 * const input = {
 *   content: "osi_spec_version: '1.0'
 * metrics:
 * - name: total_revenue
 *   description: Total revenue from closed orders
 *   expression:
 *     dialects:
 *     - dialect: ANSI_SQL
 *       expression: SELECT SUM(net_amount) FROM public.orders
 *   custom_extensions:
 *   - vendor_name: COA
 *     data:
 *       data_source_id: warehouse-pg-01
 *       source_table: public.orders
 * ",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new ImportOsiCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   datasetsResolved: 0,
 *   jobId: "01HZY8K3M4N5P6Q7R8S9T0V1W2",
 *   metricsCreated: 0,
 *   metricsUpdated: 0,
 *   status: "IN_PROGRESS"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ImportOsiCommand extends $Command
  .classBuilder<
    ImportOsiCommandInput,
    ImportOsiCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ImportOsi", {})
  .n("ControlPlaneServiceClient", "ImportOsiCommand")
  .sc(ImportOsi$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ImportOsiInput;
      output: ImportOsiOutput;
    };
    sdk: {
      input: ImportOsiCommandInput;
      output: ImportOsiCommandOutput;
    };
  };
}
