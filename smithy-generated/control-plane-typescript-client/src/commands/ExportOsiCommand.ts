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
import type { ExportOsiInput, ExportOsiOutput } from "../models/models_0";
import { ExportOsi$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ExportOsiCommand}.
 */
export interface ExportOsiCommandInput extends ExportOsiInput {}
/**
 * @public
 *
 * The output of {@link ExportOsiCommand}.
 */
export interface ExportOsiCommandOutput extends ExportOsiOutput, __MetadataBearer {}

/**
 * Export metric definitions as an OSI (Open Semantic Interchange) YAML document.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ExportOsiCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ExportOsiCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ExportOsiInput
 *   namespaceId: "STRING_VALUE", // required
 *   format: "STRING_VALUE",
 *   names: [ // MetricNameList
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new ExportOsiCommand(input);
 * const response = await client.send(command);
 * // { // ExportOsiOutput
 * //   content: "STRING_VALUE",
 * //   downloadUrl: "STRING_VALUE",
 * //   expiresIn: Number("int"),
 * // };
 *
 * ```
 *
 * @param ExportOsiCommandInput - {@link ExportOsiCommandInput}
 * @returns {@link ExportOsiCommandOutput}
 * @see {@link ExportOsiCommandInput} for command's `input` shape.
 * @see {@link ExportOsiCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
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
 * @example Export selected metrics inline
 * ```javascript
 * //
 * const input = {
 *   format: "inline",
 *   names: [
 *     "total_revenue"
 *   ],
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new ExportOsiCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   content: "osi_spec_version: '1.0'
 * datasets:
 * - name: orders
 *   source: public.orders
 *   data_source_id: warehouse-pg-01
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
 * "
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ExportOsiCommand extends $Command
  .classBuilder<
    ExportOsiCommandInput,
    ExportOsiCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ExportOsi", {})
  .n("ControlPlaneServiceClient", "ExportOsiCommand")
  .sc(ExportOsi$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ExportOsiInput;
      output: ExportOsiOutput;
    };
    sdk: {
      input: ExportOsiCommandInput;
      output: ExportOsiCommandOutput;
    };
  };
}
