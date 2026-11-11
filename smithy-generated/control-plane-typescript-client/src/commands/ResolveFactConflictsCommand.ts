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
import type { FactConflictResolutionOutcome, ResolveFactConflictsInput } from "../models/models_0";
import { ResolveFactConflicts$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ResolveFactConflictsCommand}.
 */
export interface ResolveFactConflictsCommandInput extends ResolveFactConflictsInput {}
/**
 * @public
 *
 * The output of {@link ResolveFactConflictsCommand}.
 */
export interface ResolveFactConflictsCommandOutput extends FactConflictResolutionOutcome, __MetadataBearer {}

/**
 * Adjudicate fact conflicts for this namespace.
 *
 * `keep` and `keep_both` require `subject` + `predicate`. `merge` also
 * requires `mergedObject` (an IRI unless `mergedObjectKind` is `literal`).
 * `batch` requires `keep` plus at least one scope member
 * (`predicate`, `subject` or `sourceDocumentId`) and previews by default:
 * nothing is written unless `dryRun` is false.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ResolveFactConflictsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ResolveFactConflictsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ResolveFactConflictsInput
 *   namespaceId: "STRING_VALUE", // required
 *   subject: "STRING_VALUE",
 *   predicate: "STRING_VALUE",
 *   action: "keep" || "keep_both" || "merge" || "batch", // required
 *   keep: "STRING_VALUE",
 *   mergedObject: "STRING_VALUE",
 *   mergedObjectKind: "STRING_VALUE",
 *   graph: "STRING_VALUE",
 *   sourceDocumentId: "STRING_VALUE",
 *   dryRun: true || false,
 *   actor: "STRING_VALUE",
 *   reason: "STRING_VALUE",
 * };
 * const command = new ResolveFactConflictsCommand(input);
 * const response = await client.send(command);
 * // { // FactConflictResolutionOutcome
 * //   action: "keep" || "keep_both" || "merge" || "batch", // required
 * //   subject: "STRING_VALUE",
 * //   predicate: "STRING_VALUE",
 * //   kept: "STRING_VALUE",
 * //   keptFactIds: [ // FactIdList
 * //     "STRING_VALUE",
 * //   ],
 * //   retiredFactIds: [
 * //     "STRING_VALUE",
 * //   ],
 * //   retired: Number("int"),
 * //   values: [ // FactIriList
 * //     "STRING_VALUE",
 * //   ],
 * //   acceptedFactIds: [
 * //     "STRING_VALUE",
 * //   ],
 * //   mergedFactId: "STRING_VALUE",
 * //   originalFactIds: [
 * //     "STRING_VALUE",
 * //   ],
 * //   batch: { // FactBatchKeepResult
 * //     batchId: "STRING_VALUE", // required
 * //     dryRun: true || false, // required
 * //     keep: "STRING_VALUE", // required
 * //     matched: Number("int"), // required
 * //     kept: Number("int"), // required
 * //     skipped: Number("int"), // required
 * //     affectedFacts: Number("int"), // required
 * //     subject: "STRING_VALUE",
 * //     predicate: "STRING_VALUE",
 * //     sourceDocumentId: "STRING_VALUE",
 * //     results: [ // FactBatchKeepRowList
 * //       { // FactBatchKeepRow
 * //         subject: "STRING_VALUE", // required
 * //         predicate: "STRING_VALUE", // required
 * //         status: "STRING_VALUE", // required
 * //         retired: Number("int"),
 * //         reason: "STRING_VALUE",
 * //         values: [
 * //           "STRING_VALUE",
 * //         ],
 * //         keptFactIds: [
 * //           "STRING_VALUE",
 * //         ],
 * //         retiredFactIds: "<FactIdList>",
 * //       },
 * //     ],
 * //   },
 * // };
 *
 * ```
 *
 * @param ResolveFactConflictsCommandInput - {@link ResolveFactConflictsCommandInput}
 * @returns {@link ResolveFactConflictsCommandOutput}
 * @see {@link ResolveFactConflictsCommandInput} for command's `input` shape.
 * @see {@link ResolveFactConflictsCommandOutput} for command's `response` shape.
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
 * @example Merge two conflicting values
 * ```javascript
 * //
 * const input = {
 *   action: "merge",
 *   mergedObject: "urn:coa:entity:archive",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   predicate: "urn:coa:predicate:belongs-to",
 *   subject: "urn:coa:entity:contract-ledger"
 * };
 * const command = new ResolveFactConflictsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   action: "merge",
 *   mergedFactId: "fact-1a2b3c4d5e6f",
 *   originalFactIds: [
 *     "fact-0f1e2d3c4b5a",
 *     "fact-a9b8c7d6e5f4"
 *   ],
 *   predicate: "urn:coa:predicate:belongs-to",
 *   subject: "urn:coa:entity:contract-ledger"
 * }
 * *\/
 * ```
 *
 * @example Preview a batch keep for one predicate
 * ```javascript
 * //
 * const input = {
 *   action: "batch",
 *   dryRun: true,
 *   keep: "urn:coa:entity:archive",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   predicate: "urn:coa:predicate:belongs-to"
 * };
 * const command = new ResolveFactConflictsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   action: "batch",
 *   batch: {
 *     affectedFacts: 3,
 *     batchId: "resolve-1a2b3c4d5e",
 *     dryRun: true,
 *     keep: "urn:coa:entity:archive",
 *     kept: 3,
 *     matched: 3,
 *     skipped: 0
 *   },
 *   predicate: "urn:coa:predicate:belongs-to"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ResolveFactConflictsCommand extends $Command
  .classBuilder<
    ResolveFactConflictsCommandInput,
    ResolveFactConflictsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ResolveFactConflicts", {})
  .n("ControlPlaneServiceClient", "ResolveFactConflictsCommand")
  .sc(ResolveFactConflicts$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ResolveFactConflictsInput;
      output: FactConflictResolutionOutcome;
    };
    sdk: {
      input: ResolveFactConflictsCommandInput;
      output: ResolveFactConflictsCommandOutput;
    };
  };
}
