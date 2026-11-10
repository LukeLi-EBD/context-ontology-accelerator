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
import type { ListDictionariesInput, ListDictionariesOutput } from "../models/models_0";
import { ListDictionaries$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListDictionariesCommand}.
 */
export interface ListDictionariesCommandInput extends ListDictionariesInput {}
/**
 * @public
 *
 * The output of {@link ListDictionariesCommand}.
 */
export interface ListDictionariesCommandOutput extends ListDictionariesOutput, __MetadataBearer {}

/**
 * List sources that have a dictionary snapshot.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListDictionariesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListDictionariesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListDictionariesInput
 *   namespaceId: "STRING_VALUE", // required
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new ListDictionariesCommand(input);
 * const response = await client.send(command);
 * // { // ListDictionariesOutput
 * //   items: [ // DictionarySummaryList // required
 * //     { // DictionarySummary
 * //       sourceId: "STRING_VALUE", // required
 * //       sourceKind: "STRING_VALUE", // required
 * //       tables: Number("int"), // required
 * //       columns: Number("int"), // required
 * //       commented: Number("int"), // required
 * //       bound: Number("int"), // required
 * //       observedAt: "STRING_VALUE",
 * //       lastRun: { // DictionaryRefreshRun
 * //         runId: "STRING_VALUE", // required
 * //         sourceId: "STRING_VALUE", // required
 * //         status: "STRING_VALUE", // required
 * //         idempotencyKey: "STRING_VALUE",
 * //         requestedBy: "STRING_VALUE",
 * //         startedAt: "STRING_VALUE",
 * //         finishedAt: "STRING_VALUE",
 * //         processed: Number("int"),
 * //         inserted: Number("int"),
 * //         updated: Number("int"),
 * //         unchanged: Number("int"),
 * //         removed: Number("int"),
 * //         error: "STRING_VALUE",
 * //       },
 * //     },
 * //   ],
 * //   total: Number("int"), // required
 * //   offset: Number("int"), // required
 * //   limit: Number("int"), // required
 * // };
 *
 * ```
 *
 * @param ListDictionariesCommandInput - {@link ListDictionariesCommandInput}
 * @returns {@link ListDictionariesCommandOutput}
 * @see {@link ListDictionariesCommandInput} for command's `input` shape.
 * @see {@link ListDictionariesCommandOutput} for command's `response` shape.
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
 * @example List sources that have a dictionary snapshot
 * ```javascript
 * //
 * const input = {
 *   limit: 50,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   offset: 0
 * };
 * const command = new ListDictionariesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       bound: 96,
 *       columns: 143,
 *       commented: 118,
 *       observedAt: "2026-11-10T09:15:00Z",
 *       sourceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *       sourceKind: "postgresql",
 *       tables: 12
 *     }
 *   ],
 *   limit: 50,
 *   offset: 0,
 *   total: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListDictionariesCommand extends $Command
  .classBuilder<
    ListDictionariesCommandInput,
    ListDictionariesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListDictionaries", {})
  .n("ControlPlaneServiceClient", "ListDictionariesCommand")
  .sc(ListDictionaries$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListDictionariesInput;
      output: ListDictionariesOutput;
    };
    sdk: {
      input: ListDictionariesCommandInput;
      output: ListDictionariesCommandOutput;
    };
  };
}
