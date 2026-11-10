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
import type { GetDictionaryViewInput, GetDictionaryViewOutput } from "../models/models_0";
import { GetDictionaryView$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetDictionaryViewCommand}.
 */
export interface GetDictionaryViewCommandInput extends GetDictionaryViewInput {}
/**
 * @public
 *
 * The output of {@link GetDictionaryViewCommand}.
 */
export interface GetDictionaryViewCommandOutput extends GetDictionaryViewOutput, __MetadataBearer {}

/**
 * Page the column view with the four dashboard filters (F60/F61/F64/F65).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetDictionaryViewCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetDictionaryViewCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetDictionaryViewInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   view: "STRING_VALUE",
 *   table: "STRING_VALUE",
 *   column: "STRING_VALUE",
 *   bindingMethod: "STRING_VALUE",
 *   sourceKind: "STRING_VALUE",
 *   query: "STRING_VALUE",
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new GetDictionaryViewCommand(input);
 * const response = await client.send(command);
 * // { // GetDictionaryViewOutput
 * //   items: [ // DictionaryColumnList // required
 * //     { // DictionaryColumn
 * //       sourceId: "STRING_VALUE", // required
 * //       catalog: "STRING_VALUE", // required
 * //       schema: "STRING_VALUE", // required
 * //       table: "STRING_VALUE", // required
 * //       column: "STRING_VALUE", // required
 * //       dataType: "STRING_VALUE", // required
 * //       isNullable: true || false, // required
 * //       sourceKind: "STRING_VALUE", // required
 * //       bindingMethod: "STRING_VALUE", // required
 * //       comment: "STRING_VALUE",
 * //       propertyIri: "STRING_VALUE",
 * //       confidence: Number("double"),
 * //       bindingNote: "STRING_VALUE",
 * //       observedAt: "STRING_VALUE",
 * //       lastRefreshRunId: "STRING_VALUE",
 * //     },
 * //   ],
 * //   total: Number("int"), // required
 * //   offset: Number("int"), // required
 * //   limit: Number("int"), // required
 * //   view: "STRING_VALUE", // required
 * //   coverage: { // CommentCoverage
 * //     total: Number("int"), // required
 * //     commented: Number("int"), // required
 * //     missing: Number("int"), // required
 * //     ratio: Number("double"),
 * //   },
 * //   warnings: [ // StringList
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param GetDictionaryViewCommandInput - {@link GetDictionaryViewCommandInput}
 * @returns {@link GetDictionaryViewCommandOutput}
 * @see {@link GetDictionaryViewCommandInput} for command's `input` shape.
 * @see {@link GetDictionaryViewCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Page columns that are missing a comment
 * ```javascript
 * //
 * const input = {
 *   limit: 50,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0,
 *   sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d",
 *   view: "missing_comment"
 * };
 * const command = new GetDictionaryViewCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   coverage: {
 *     commented: 20,
 *     missing: 1,
 *     ratio: 0.952,
 *     total: 21
 *   },
 *   items: [
 *     {
 *       bindingMethod: "none",
 *       catalog: "analytics",
 *       column: "legacy_flag",
 *       dataType: "boolean",
 *       isNullable: true,
 *       observedAt: "2026-11-10T09:15:00Z",
 *       schema: "public",
 *       sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d",
 *       sourceKind: "postgresql",
 *       table: "loan_account"
 *     }
 *   ],
 *   limit: 50,
 *   offset: 0,
 *   total: 1,
 *   view: "missing_comment"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetDictionaryViewCommand extends $Command
  .classBuilder<
    GetDictionaryViewCommandInput,
    GetDictionaryViewCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetDictionaryView", {})
  .n("ControlPlaneServiceClient", "GetDictionaryViewCommand")
  .sc(GetDictionaryView$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetDictionaryViewInput;
      output: GetDictionaryViewOutput;
    };
    sdk: {
      input: GetDictionaryViewCommandInput;
      output: GetDictionaryViewCommandOutput;
    };
  };
}
