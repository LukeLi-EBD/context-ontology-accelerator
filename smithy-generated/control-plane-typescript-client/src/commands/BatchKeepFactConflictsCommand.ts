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
import type { BatchKeepFactConflictsInput, FactBatchKeepResult } from "../models/models_0";
import { BatchKeepFactConflicts$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link BatchKeepFactConflictsCommand}.
 */
export interface BatchKeepFactConflictsCommandInput extends BatchKeepFactConflictsInput {}
/**
 * @public
 *
 * The output of {@link BatchKeepFactConflictsCommand}.
 */
export interface BatchKeepFactConflictsCommandOutput extends FactBatchKeepResult, __MetadataBearer {}

/**
 * Apply one explicit `keep A` rule to every pending conflict in a scope.
 *
 * This is the dedicated `/facts/conflicts/batch` route. It uses the same
 * ledger transaction as `ResolveFactConflicts` with `action: "batch"`; the
 * route is kept because early callers post here directly. `dryRun` defaults
 * to true, so an omitted flag can only preview.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, BatchKeepFactConflictsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, BatchKeepFactConflictsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // BatchKeepFactConflictsInput
 *   namespaceId: "STRING_VALUE", // required
 *   keep: "STRING_VALUE", // required
 *   predicate: "STRING_VALUE",
 *   subject: "STRING_VALUE",
 *   sourceDocumentId: "STRING_VALUE",
 *   actor: "STRING_VALUE",
 *   reason: "STRING_VALUE",
 *   dryRun: true || false,
 * };
 * const command = new BatchKeepFactConflictsCommand(input);
 * const response = await client.send(command);
 * // { // FactBatchKeepResult
 * //   batchId: "STRING_VALUE", // required
 * //   dryRun: true || false, // required
 * //   keep: "STRING_VALUE", // required
 * //   matched: Number("int"), // required
 * //   kept: Number("int"), // required
 * //   skipped: Number("int"), // required
 * //   affectedFacts: Number("int"), // required
 * //   subject: "STRING_VALUE",
 * //   predicate: "STRING_VALUE",
 * //   sourceDocumentId: "STRING_VALUE",
 * //   results: [ // FactBatchKeepRowList
 * //     { // FactBatchKeepRow
 * //       subject: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       status: "STRING_VALUE", // required
 * //       retired: Number("int"),
 * //       reason: "STRING_VALUE",
 * //       values: [ // FactIriList
 * //         "STRING_VALUE",
 * //       ],
 * //       keptFactIds: [ // FactIdList
 * //         "STRING_VALUE",
 * //       ],
 * //       retiredFactIds: [
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param BatchKeepFactConflictsCommandInput - {@link BatchKeepFactConflictsCommandInput}
 * @returns {@link BatchKeepFactConflictsCommandOutput}
 * @see {@link BatchKeepFactConflictsCommandInput} for command's `input` shape.
 * @see {@link BatchKeepFactConflictsCommandOutput} for command's `response` shape.
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
 * @example Preview a batch keep
 * ```javascript
 * //
 * const input = {
 *   actor: "operator",
 *   dryRun: true,
 *   keep: "urn:coa:entity:archive",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   predicate: "urn:coa:predicate:belongs-to",
 *   reason: "archive is the canonical owner"
 * };
 * const command = new BatchKeepFactConflictsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   affectedFacts: 0,
 *   batchId: "resolve-1a2b3c4d5e",
 *   dryRun: true,
 *   keep: "urn:coa:entity:archive",
 *   kept: 1,
 *   matched: 1,
 *   predicate: "urn:coa:predicate:belongs-to",
 *   results: [
 *     {
 *       predicate: "urn:coa:predicate:belongs-to",
 *       retired: 0,
 *       status: "would_keep",
 *       subject: "urn:coa:entity:contract-ledger",
 *       values: [
 *         "urn:coa:entity:archive",
 *         "urn:coa:entity:legal"
 *       ]
 *     }
 *   ],
 *   skipped: 0
 * }
 * *\/
 * ```
 *
 * @public
 */
export class BatchKeepFactConflictsCommand extends $Command
  .classBuilder<
    BatchKeepFactConflictsCommandInput,
    BatchKeepFactConflictsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "BatchKeepFactConflicts", {})
  .n("ControlPlaneServiceClient", "BatchKeepFactConflictsCommand")
  .sc(BatchKeepFactConflicts$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: BatchKeepFactConflictsInput;
      output: FactBatchKeepResult;
    };
    sdk: {
      input: BatchKeepFactConflictsCommandInput;
      output: BatchKeepFactConflictsCommandOutput;
    };
  };
}
