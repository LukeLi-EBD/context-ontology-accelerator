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
import type { FactBatchRetractResult, RetractFactsInput } from "../models/models_0";
import { RetractFacts$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RetractFactsCommand}.
 */
export interface RetractFactsCommandInput extends RetractFactsInput {}
/**
 * @public
 *
 * The output of {@link RetractFactsCommand}.
 */
export interface RetractFactsCommandOutput extends FactBatchRetractResult, __MetadataBearer {}

/**
 * Withdraw many assertion rows in one ledger transaction.
 *
 * Selection is either an explicit `factIds` list or the `subject`,
 * `predicate`, `graph` and `sourceDocumentId` filters. `dryRun` defaults to
 * true so an omitted flag can only preview the change.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RetractFactsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RetractFactsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RetractFactsInput
 *   namespaceId: "STRING_VALUE", // required
 *   factIds: [ // FactIdList
 *     "STRING_VALUE",
 *   ],
 *   subject: "STRING_VALUE",
 *   predicate: "STRING_VALUE",
 *   graph: "STRING_VALUE",
 *   sourceDocumentId: "STRING_VALUE",
 *   actor: "STRING_VALUE",
 *   reason: "STRING_VALUE",
 *   dryRun: true || false,
 * };
 * const command = new RetractFactsCommand(input);
 * const response = await client.send(command);
 * // { // FactBatchRetractResult
 * //   dryRun: true || false, // required
 * //   batchId: "STRING_VALUE",
 * //   count: Number("int"), // required
 * //   items: [ // FactRetractItemList // required
 * //     { // FactRetractItem
 * //       factId: "STRING_VALUE", // required
 * //       subject: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       object: "STRING_VALUE", // required
 * //       objectKind: "STRING_VALUE", // required
 * //       graph: "STRING_VALUE", // required
 * //       candidateId: "STRING_VALUE",
 * //     },
 * //   ],
 * //   skipped: [ // FactRetractSkippedList // required
 * //     { // FactRetractSkipped
 * //       factId: "STRING_VALUE", // required
 * //       reason: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   actor: "STRING_VALUE", // required
 * //   reason: "STRING_VALUE",
 * //   retracted: [ // FactIdList
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param RetractFactsCommandInput - {@link RetractFactsCommandInput}
 * @returns {@link RetractFactsCommandOutput}
 * @see {@link RetractFactsCommandInput} for command's `input` shape.
 * @see {@link RetractFactsCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Preview retracting one source's facts
 * ```javascript
 * //
 * const input = {
 *   actor: "operator",
 *   dryRun: true,
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   reason: "source withdrawn",
 *   sourceDocumentId: "8c7d6e5f-4a3b-4c2d-8e1f-0a9b8c7d6e5f"
 * };
 * const command = new RetractFactsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   actor: "operator",
 *   count: 1,
 *   dryRun: true,
 *   items: [
 *     {
 *       factId: "fact-1a2b3c4d5e6f",
 *       graph: "urn:coa:graph:asserted",
 *       object: "urn:coa:entity:archive",
 *       objectKind: "iri",
 *       predicate: "urn:coa:predicate:belongs-to",
 *       subject: "urn:coa:entity:contract-ledger"
 *     }
 *   ],
 *   reason: "source withdrawn",
 *   skipped:   []
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RetractFactsCommand extends $Command
  .classBuilder<
    RetractFactsCommandInput,
    RetractFactsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RetractFacts", {})
  .n("ControlPlaneServiceClient", "RetractFactsCommand")
  .sc(RetractFacts$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RetractFactsInput;
      output: FactBatchRetractResult;
    };
    sdk: {
      input: RetractFactsCommandInput;
      output: RetractFactsCommandOutput;
    };
  };
}
