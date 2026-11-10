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
import type { GetDictionaryCommentCoverageInput, GetDictionaryCommentCoverageOutput } from "../models/models_0";
import { GetDictionaryCommentCoverage$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetDictionaryCommentCoverageCommand}.
 */
export interface GetDictionaryCommentCoverageCommandInput extends GetDictionaryCommentCoverageInput {}
/**
 * @public
 *
 * The output of {@link GetDictionaryCommentCoverageCommand}.
 */
export interface GetDictionaryCommentCoverageCommandOutput extends GetDictionaryCommentCoverageOutput, __MetadataBearer {}

/**
 * Comment coverage for one source (F66).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetDictionaryCommentCoverageCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetDictionaryCommentCoverageCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetDictionaryCommentCoverageInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   table: "STRING_VALUE",
 * };
 * const command = new GetDictionaryCommentCoverageCommand(input);
 * const response = await client.send(command);
 * // { // GetDictionaryCommentCoverageOutput
 * //   sourceId: "STRING_VALUE", // required
 * //   coverage: { // CommentCoverage
 * //     total: Number("int"), // required
 * //     commented: Number("int"), // required
 * //     missing: Number("int"), // required
 * //     ratio: Number("double"),
 * //   },
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
 * // };
 *
 * ```
 *
 * @param GetDictionaryCommentCoverageCommandInput - {@link GetDictionaryCommentCoverageCommandInput}
 * @returns {@link GetDictionaryCommentCoverageCommandOutput}
 * @see {@link GetDictionaryCommentCoverageCommandInput} for command's `input` shape.
 * @see {@link GetDictionaryCommentCoverageCommandOutput} for command's `response` shape.
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
 * @example Comment coverage for one source
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d"
 * };
 * const command = new GetDictionaryCommentCoverageCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   coverage: {
 *     commented: 118,
 *     missing: 25,
 *     ratio: 0.825,
 *     total: 143
 *   },
 *   sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d",
 *   tables: [
 *     {
 *       bound: 18,
 *       columns: 21,
 *       commented: 20,
 *       missingComment: 1,
 *       table: "loan_account",
 *       unbound: 3
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetDictionaryCommentCoverageCommand extends $Command
  .classBuilder<
    GetDictionaryCommentCoverageCommandInput,
    GetDictionaryCommentCoverageCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetDictionaryCommentCoverage", {})
  .n("ControlPlaneServiceClient", "GetDictionaryCommentCoverageCommand")
  .sc(GetDictionaryCommentCoverage$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetDictionaryCommentCoverageInput;
      output: GetDictionaryCommentCoverageOutput;
    };
    sdk: {
      input: GetDictionaryCommentCoverageCommandInput;
      output: GetDictionaryCommentCoverageCommandOutput;
    };
  };
}
