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
import type { FactEventPage, ListFactEventsInput } from "../models/models_0";
import { ListFactEvents$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListFactEventsCommand}.
 */
export interface ListFactEventsCommandInput extends ListFactEventsInput {}
/**
 * @public
 *
 * The output of {@link ListFactEventsCommand}.
 */
export interface ListFactEventsCommandOutput extends FactEventPage, __MetadataBearer {}

/**
 * Read one page of a fact's hash-chained event history.
 *
 * Events are returned newest first. Pass `nextBefore` back as `before` to page
 * further back in the chain.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListFactEventsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListFactEventsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListFactEventsInput
 *   namespaceId: "STRING_VALUE", // required
 *   factId: "STRING_VALUE", // required
 *   limit: Number("int"),
 *   before: Number("int"),
 *   format: "full" || "summary",
 * };
 * const command = new ListFactEventsCommand(input);
 * const response = await client.send(command);
 * // { // FactEventPage
 * //   factId: "STRING_VALUE", // required
 * //   count: Number("int"), // required
 * //   total: Number("int"), // required
 * //   items: [ // FactEventList // required
 * //     { // FactEvent
 * //       eventId: Number("int"), // required
 * //       factId: "STRING_VALUE", // required
 * //       action: "STRING_VALUE", // required
 * //       actor: "STRING_VALUE",
 * //       reason: "STRING_VALUE",
 * //       batchId: "STRING_VALUE",
 * //       payload: "DOCUMENT_VALUE",
 * //       prevEvent: Number("int"),
 * //       hash: "STRING_VALUE",
 * //       createdAt: "STRING_VALUE",
 * //     },
 * //   ],
 * //   nextBefore: Number("int"),
 * // };
 *
 * ```
 *
 * @param ListFactEventsCommandInput - {@link ListFactEventsCommandInput}
 * @returns {@link ListFactEventsCommandOutput}
 * @see {@link ListFactEventsCommandInput} for command's `input` shape.
 * @see {@link ListFactEventsCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
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
 * @example Read a fact's event chain
 * ```javascript
 * //
 * const input = {
 *   factId: "fact-1a2b3c4d5e6f",
 *   format: "summary",
 *   limit: 20,
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new ListFactEventsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   count: 1,
 *   factId: "fact-1a2b3c4d5e6f",
 *   items: [
 *     {
 *       action: "assert",
 *       actor: "operator",
 *       createdAt: "2026-10-01T08:00:00Z",
 *       eventId: 41,
 *       factId: "fact-1a2b3c4d5e6f"
 *     }
 *   ],
 *   total: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListFactEventsCommand extends $Command
  .classBuilder<
    ListFactEventsCommandInput,
    ListFactEventsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListFactEvents", {})
  .n("ControlPlaneServiceClient", "ListFactEventsCommand")
  .sc(ListFactEvents$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListFactEventsInput;
      output: FactEventPage;
    };
    sdk: {
      input: ListFactEventsCommandInput;
      output: ListFactEventsCommandOutput;
    };
  };
}
