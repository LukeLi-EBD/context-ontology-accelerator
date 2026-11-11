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
import type { ListIngestionRunsInput, ListIngestionRunsOutput } from "../models/models_0";
import { ListIngestionRuns$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListIngestionRunsCommand}.
 */
export interface ListIngestionRunsCommandInput extends ListIngestionRunsInput {}
/**
 * @public
 *
 * The output of {@link ListIngestionRunsCommand}.
 */
export interface ListIngestionRunsCommandOutput extends ListIngestionRunsOutput, __MetadataBearer {}

/**
 * List namespace-scoped ingestion runs (F17) with counters that refresh on
 * each call (F18), newest first.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListIngestionRunsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListIngestionRunsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListIngestionRunsInput
 *   namespaceId: "STRING_VALUE", // required
 *   kind: "BATCH",
 *   status: "RUNNING" || "COMPLETED" || "INTERRUPTED" || "STALE",
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListIngestionRunsCommand(input);
 * const response = await client.send(command);
 * // { // ListIngestionRunsOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // IngestionRunList // required
 * //     { // IngestionRun
 * //       runId: "STRING_VALUE", // required
 * //       root: "STRING_VALUE", // required
 * //       status: "RUNNING" || "COMPLETED" || "INTERRUPTED" || "STALE", // required
 * //       stale: true || false, // required
 * //       staleReason: "STRING_VALUE",
 * //       total: Number("long"), // required
 * //       completed: Number("long"), // required
 * //       indexed: Number("long"), // required
 * //       failed: Number("long"), // required
 * //       degraded: Number("long"), // required
 * //       createdAt: new Date("TIMESTAMP"), // required
 * //       updatedAt: new Date("TIMESTAMP"), // required
 * //       finishedAt: new Date("TIMESTAMP"),
 * //       lastRun: { // IngestionRunAttempt
 * //         runId: "STRING_VALUE", // required
 * //         status: "RUNNING" || "COMPLETED" || "INTERRUPTED" || "FAILED", // required
 * //         startedAt: new Date("TIMESTAMP"), // required
 * //         finishedAt: new Date("TIMESTAMP"),
 * //         exitCode: Number("int"),
 * //         errorCode: "STRING_VALUE",
 * //         errorMessage: "STRING_VALUE",
 * //         counters: { // IngestionRunCounters
 * //           total: Number("long"), // required
 * //           alreadyDone: Number("long"), // required
 * //           processed: Number("long"), // required
 * //           parsed: Number("long"), // required
 * //           resumedChunked: Number("long"), // required
 * //           indexed: Number("long"), // required
 * //           documentsAdded: Number("long"), // required
 * //           failedThisRun: Number("long"), // required
 * //           failedTotal: Number("long"), // required
 * //           remainingFiles: Number("long"), // required
 * //           interrupted: true || false, // required
 * //           skipped: { // IngestionRunSkipped
 * //             hidden: Number("long"), // required
 * //             unsupported: Number("long"), // required
 * //             empty: Number("long"), // required
 * //             tooLarge: Number("long"), // required
 * //             unreadable: Number("long"), // required
 * //           },
 * //           elapsedSeconds: Number("double"), // required
 * //         },
 * //       },
 * //     },
 * //   ],
 * //   totalCount: Number("long"), // required
 * //   failures: [ // IngestionFailureList // required
 * //     { // IngestionFailure
 * //       runId: "STRING_VALUE", // required
 * //       relPath: "STRING_VALUE", // required
 * //       attempts: Number("int"), // required
 * //       code: "STRING_VALUE",
 * //       message: "STRING_VALUE",
 * //       updatedAt: new Date("TIMESTAMP"), // required
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListIngestionRunsCommandInput - {@link ListIngestionRunsCommandInput}
 * @returns {@link ListIngestionRunsCommandOutput}
 * @see {@link ListIngestionRunsCommandInput} for command's `input` shape.
 * @see {@link ListIngestionRunsCommandOutput} for command's `response` shape.
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
 * @example List one namespace's import batches
 * ```javascript
 * //
 * const input = {
 *   kind: "BATCH",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new ListIngestionRunsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   failures: [
 *     {
 *       attempts: 3,
 *       code: "E_PARSE_UNSUPPORTED",
 *       message: "unsupported legacy document format",
 *       relPath: "appendix/legacy.docx",
 *       runId: "9a7c2b40-6d1e-4b9f-8a3c-2f4d5e6a7b8c",
 *       updatedAt: "2025-11-11T00:00:00Z"
 *     }
 *   ],
 *   items: [
 *     {
 *       completed: 120,
 *       createdAt: "2025-11-10T00:00:00Z",
 *       degraded: 1,
 *       failed: 2,
 *       finishedAt: "2025-11-11T00:00:00Z",
 *       indexed: 118,
 *       root: "/data/corpus/handbook",
 *       runId: "9a7c2b40-6d1e-4b9f-8a3c-2f4d5e6a7b8c",
 *       stale: false,
 *       status: "COMPLETED",
 *       total: 120,
 *       updatedAt: "2025-11-11T00:00:00Z"
 *     }
 *   ],
 *   totalCount: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListIngestionRunsCommand extends $Command
  .classBuilder<
    ListIngestionRunsCommandInput,
    ListIngestionRunsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListIngestionRuns", {})
  .n("ControlPlaneServiceClient", "ListIngestionRunsCommand")
  .sc(ListIngestionRuns$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListIngestionRunsInput;
      output: ListIngestionRunsOutput;
    };
    sdk: {
      input: ListIngestionRunsCommandInput;
      output: ListIngestionRunsCommandOutput;
    };
  };
}
