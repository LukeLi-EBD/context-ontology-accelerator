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
import type { ListInductionJobsInput, ListInductionJobsOutput } from "../models/models_1";
import { ListInductionJobs$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListInductionJobsCommand}.
 */
export interface ListInductionJobsCommandInput extends ListInductionJobsInput {}
/**
 * @public
 *
 * The output of {@link ListInductionJobsCommand}.
 */
export interface ListInductionJobsCommandOutput extends ListInductionJobsOutput, __MetadataBearer {}

/**
 * List induction jobs for a namespace, one page at a time.
 *
 * A page can hold fewer than `maxResults` jobs, or none, while `nextToken` is
 * present: each request reads a bounded slice of the job table. Keep paging
 * until `nextToken` is absent. Jobs are newest-first within a page only.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListInductionJobsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListInductionJobsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListInductionJobsInput
 *   namespaceId: "STRING_VALUE", // required
 *   status: "pending" || "fetching_metadata" || "loading_grounding_ontologies" || "generating_embeddings" || "matching" || "building_ontology" || "storing" || "completed" || "failed" || "querying_neptune" || "sampling" || "generating_descriptions" || "resolving_iris" || "applying_rules" || "entailment" || "serializing" || "running",
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListInductionJobsCommand(input);
 * const response = await client.send(command);
 * // { // ListInductionJobsOutput
 * //   nextToken: "STRING_VALUE",
 * //   jobs: [ // InductionJobSummaryList // required
 * //     { // InductionJobSummary
 * //       jobId: "STRING_VALUE", // required
 * //       status: "pending" || "fetching_metadata" || "loading_grounding_ontologies" || "generating_embeddings" || "matching" || "building_ontology" || "storing" || "completed" || "failed" || "querying_neptune" || "sampling" || "generating_descriptions" || "resolving_iris" || "applying_rules" || "entailment" || "serializing" || "running", // required
 * //       createdAt: new Date("TIMESTAMP"), // required
 * //       sourceType: "STRUCTURED" || "UNSTRUCTURED" || "BRIDGE",
 * //       tablesProcessed: Number("int"),
 * //       novelClassesCreated: Number("int"),
 * //       error: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListInductionJobsCommandInput - {@link ListInductionJobsCommandInput}
 * @returns {@link ListInductionJobsCommandOutput}
 * @see {@link ListInductionJobsCommandInput} for command's `input` shape.
 * @see {@link ListInductionJobsCommandOutput} for command's `response` shape.
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
 * @example List completed induction jobs
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   status: "completed"
 * };
 * const command = new ListInductionJobsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   jobs: [
 *     {
 *       createdAt: "2026-07-23T14:30:00Z",
 *       jobId: "3f8a1c2d-9b4e-4a6f-8c1d-2e5f7a9b0c3d",
 *       novelClassesCreated: 7,
 *       sourceType: "STRUCTURED",
 *       status: "completed",
 *       tablesProcessed: 12
 *     }
 *   ],
 *   nextToken: "eyJvZmZzZXQiOiAyMH0="
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListInductionJobsCommand extends $Command
  .classBuilder<
    ListInductionJobsCommandInput,
    ListInductionJobsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListInductionJobs", {})
  .n("ControlPlaneServiceClient", "ListInductionJobsCommand")
  .sc(ListInductionJobs$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListInductionJobsInput;
      output: ListInductionJobsOutput;
    };
    sdk: {
      input: ListInductionJobsCommandInput;
      output: ListInductionJobsCommandOutput;
    };
  };
}
