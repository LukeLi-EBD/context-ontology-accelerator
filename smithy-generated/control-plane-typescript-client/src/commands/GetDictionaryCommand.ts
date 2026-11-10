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
import type { GetDictionaryInput, GetDictionaryOutput } from "../models/models_0";
import { GetDictionary$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetDictionaryCommand}.
 */
export interface GetDictionaryCommandInput extends GetDictionaryInput {}
/**
 * @public
 *
 * The output of {@link GetDictionaryCommand}.
 */
export interface GetDictionaryCommandOutput extends GetDictionaryOutput, __MetadataBearer {}

/**
 * Describe one source's dictionary: table rollups + exact comment coverage.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetDictionaryCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetDictionaryCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetDictionaryInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   table: "STRING_VALUE",
 * };
 * const command = new GetDictionaryCommand(input);
 * const response = await client.send(command);
 * // { // GetDictionaryOutput
 * //   sourceId: "STRING_VALUE", // required
 * //   sourceKind: "STRING_VALUE",
 * //   catalog: "STRING_VALUE",
 * //   schema: "STRING_VALUE",
 * //   tables: [ // DictionaryTableSummaryList // required
 * //     { // DictionaryTableSummary
 * //       table: "STRING_VALUE", // required
 * //       columns: Number("int"), // required
 * //       commented: Number("int"), // required
 * //       bound: Number("int"), // required
 * //       missingComment: Number("int"), // required
 * //       unbound: Number("int"), // required
 * //     },
 * //   ],
 * //   totals: { // CommentCoverage
 * //     total: Number("int"), // required
 * //     commented: Number("int"), // required
 * //     missing: Number("int"), // required
 * //     ratio: Number("double"),
 * //   },
 * //   boundColumns: Number("int"), // required
 * //   latestRun: { // DictionaryRefreshRun
 * //     runId: "STRING_VALUE", // required
 * //     sourceId: "STRING_VALUE", // required
 * //     status: "STRING_VALUE", // required
 * //     idempotencyKey: "STRING_VALUE",
 * //     requestedBy: "STRING_VALUE",
 * //     startedAt: "STRING_VALUE",
 * //     finishedAt: "STRING_VALUE",
 * //     processed: Number("int"),
 * //     inserted: Number("int"),
 * //     updated: Number("int"),
 * //     unchanged: Number("int"),
 * //     removed: Number("int"),
 * //     error: "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param GetDictionaryCommandInput - {@link GetDictionaryCommandInput}
 * @returns {@link GetDictionaryCommandOutput}
 * @see {@link GetDictionaryCommandInput} for command's `input` shape.
 * @see {@link GetDictionaryCommandOutput} for command's `response` shape.
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
 * @example Describe one source's dictionary
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d"
 * };
 * const command = new GetDictionaryCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   boundColumns: 18,
 *   catalog: "analytics",
 *   schema: "public",
 *   sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d",
 *   sourceKind: "postgresql",
 *   tables: [
 *     {
 *       bound: 18,
 *       columns: 21,
 *       commented: 20,
 *       missingComment: 1,
 *       table: "loan_account",
 *       unbound: 3
 *     }
 *   ],
 *   totals: {
 *     commented: 20,
 *     missing: 1,
 *     ratio: 0.952,
 *     total: 21
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetDictionaryCommand extends $Command
  .classBuilder<
    GetDictionaryCommandInput,
    GetDictionaryCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetDictionary", {})
  .n("ControlPlaneServiceClient", "GetDictionaryCommand")
  .sc(GetDictionary$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetDictionaryInput;
      output: GetDictionaryOutput;
    };
    sdk: {
      input: GetDictionaryCommandInput;
      output: GetDictionaryCommandOutput;
    };
  };
}
