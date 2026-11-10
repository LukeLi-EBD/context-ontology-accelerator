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
import type { ListTermsInput, ListTermsOutput } from "../models/models_0";
import { ListTerms$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListTermsCommand}.
 */
export interface ListTermsCommandInput extends ListTermsInput {}
/**
 * @public
 *
 * The output of {@link ListTermsCommand}.
 */
export interface ListTermsCommandOutput extends ListTermsOutput, __MetadataBearer {}

/**
 * List the namespace's alias entries with anchor-class counts (F58/F59).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListTermsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListTermsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListTermsInput
 *   namespaceId: "STRING_VALUE", // required
 *   query: "STRING_VALUE",
 *   status: "STRING_VALUE",
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new ListTermsCommand(input);
 * const response = await client.send(command);
 * // { // ListTermsOutput
 * //   namespaceId: "STRING_VALUE", // required
 * //   graph: "STRING_VALUE",
 * //   counts: { // TermCounts
 * //     anchorClasses: Number("int"), // required
 * //     termEntries: Number("int"), // required
 * //     evidenced: Number("int"), // required
 * //     inferred: Number("int"), // required
 * //   },
 * //   entries: [ // TermEntryList // required
 * //     { // TermEntry
 * //       entry: "STRING_VALUE", // required
 * //       classIri: "STRING_VALUE",
 * //       classLabel: "STRING_VALUE",
 * //       label: "STRING_VALUE", // required
 * //       status: "STRING_VALUE", // required
 * //       confidence: Number("double"),
 * //       guardRegex: "STRING_VALUE",
 * //       canonicalFor: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
 * //       suppressedSurface: [
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * //   total: Number("int"), // required
 * //   offset: Number("int"), // required
 * //   limit: Number("int"), // required
 * // };
 *
 * ```
 *
 * @param ListTermsCommandInput - {@link ListTermsCommandInput}
 * @returns {@link ListTermsCommandOutput}
 * @see {@link ListTermsCommandInput} for command's `input` shape.
 * @see {@link ListTermsCommandOutput} for command's `response` shape.
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
 * @example List the first page of alias entries
 * ```javascript
 * //
 * const input = {
 *   limit: 100,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0
 * };
 * const command = new ListTermsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   counts: {
 *     anchorClasses: 42,
 *     evidenced: 261,
 *     inferred: 57,
 *     termEntries: 318
 *   },
 *   entries: [
 *     {
 *       classIri: "https://coa.local/ontology#Customer",
 *       classLabel: "Customer",
 *       confidence: 0.98,
 *       entry: "https://coa.local/term/customer",
 *       label: "客户",
 *       status: "evidenced"
 *     }
 *   ],
 *   graph: "https://coa.local/graph/lexicon",
 *   limit: 100,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0,
 *   total: 318
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListTermsCommand extends $Command
  .classBuilder<
    ListTermsCommandInput,
    ListTermsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListTerms", {})
  .n("ControlPlaneServiceClient", "ListTermsCommand")
  .sc(ListTerms$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListTermsInput;
      output: ListTermsOutput;
    };
    sdk: {
      input: ListTermsCommandInput;
      output: ListTermsCommandOutput;
    };
  };
}
