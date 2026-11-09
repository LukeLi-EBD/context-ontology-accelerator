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
import type { GetInductionJobInput, GetInductionJobOutput } from "../models/models_0";
import { GetInductionJob$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetInductionJobCommand}.
 */
export interface GetInductionJobCommandInput extends GetInductionJobInput {}
/**
 * @public
 *
 * The output of {@link GetInductionJobCommand}.
 */
export interface GetInductionJobCommandOutput extends GetInductionJobOutput, __MetadataBearer {}

/**
 * Get the status and results of an induction job.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetInductionJobCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetInductionJobCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetInductionJobInput
 *   namespaceId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 *   include: "report" || "full",
 * };
 * const command = new GetInductionJobCommand(input);
 * const response = await client.send(command);
 * // { // GetInductionJobOutput
 * //   jobId: "STRING_VALUE", // required
 * //   status: "pending" || "fetching_metadata" || "loading_grounding_ontologies" || "generating_embeddings" || "matching" || "building_ontology" || "storing" || "completed" || "failed" || "querying_neptune" || "sampling" || "generating_descriptions" || "resolving_iris" || "applying_rules" || "entailment" || "serializing" || "running", // required
 * //   createdAt: new Date("TIMESTAMP"), // required
 * //   report: { // InductionReport
 * //     tablesProcessed: Number("int"), // required
 * //     columnsProcessed: Number("int"), // required
 * //     novelClassesCreated: Number("int"), // required
 * //     matches: [ // ConceptMatchList // required
 * //       { // ConceptMatch
 * //         sourceTable: "STRING_VALUE", // required
 * //         sourceTableIdentity: "STRING_VALUE",
 * //         sourceColumn: "STRING_VALUE", // required
 * //         matchedClassUri: "STRING_VALUE",
 * //         matchedOntologyId: "STRING_VALUE",
 * //         similarity: Number("float"),
 * //         matchType: "exact" || "high_confidence" || "ambiguous" || "novel", // required
 * //       },
 * //     ],
 * //     groundingOntologiesUsed: [ // OntologyIdList
 * //       "STRING_VALUE",
 * //     ],
 * //     inducedOntologyId: "STRING_VALUE",
 * //     droppedTables: [ // DroppedTableList
 * //       { // DroppedTable
 * //         tableName: "STRING_VALUE", // required
 * //         reason: "STRING_VALUE", // required
 * //       },
 * //     ],
 * //   },
 * //   sourceType: "STRUCTURED" || "UNSTRUCTURED" || "BRIDGE",
 * //   progress: "STRING_VALUE",
 * //   bridgeReport: { // BridgeReport
 * //     ontologyId: "STRING_VALUE",
 * //     dryRun: true || false,
 * //     proposalId: "STRING_VALUE",
 * //     tablesConsidered: Number("int"),
 * //     tablesWithEvidence: Number("int"),
 * //     tablesWithoutEvidence: [ // StringList
 * //       "STRING_VALUE",
 * //     ],
 * //     tableDefinitions: Number("int"),
 * //     columnDefinitions: Number("int"),
 * //     replacedBoilerplate: Number("int"),
 * //     replacedByRule: Number("int"),
 * //     replacedByModel: Number("int"),
 * //     replacedByModelSubjects: [
 * //       "STRING_VALUE",
 * //     ],
 * //     appendedToExisting: Number("int"),
 * //     tableLinks: Number("int"),
 * //     columnLinks: Number("int"),
 * //     definedTables: [
 * //       "STRING_VALUE",
 * //     ],
 * //     definedColumns: [
 * //       "STRING_VALUE",
 * //     ],
 * //     links: [
 * //       "STRING_VALUE",
 * //     ],
 * //     llmCalls: Number("int"),
 * //     llmFailures: Number("int"),
 * //     firstLlmError: "STRING_VALUE",
 * //     failedTables: "<StringList>",
 * //     notes: "<StringList>",
 * //     elapsedSeconds: Number("int"),
 * //   },
 * //   error: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param GetInductionJobCommandInput - {@link GetInductionJobCommandInput}
 * @returns {@link GetInductionJobCommandOutput}
 * @see {@link GetInductionJobCommandInput} for command's `input` shape.
 * @see {@link GetInductionJobCommandOutput} for command's `response` shape.
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
 * @example Get a completed induction job with its report
 * ```javascript
 * //
 * const input = {
 *   jobId: "3f8a1c2d-9b4e-4a6f-8c1d-2e5f7a9b0c3d",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetInductionJobCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   createdAt: "2026-07-23T14:30:00Z",
 *   jobId: "3f8a1c2d-9b4e-4a6f-8c1d-2e5f7a9b0c3d",
 *   report: {
 *     columnsProcessed: 84,
 *     groundingOntologiesUsed: [
 *       "schema-org-core"
 *     ],
 *     inducedOntologyId: "ont-sales-2026",
 *     matches: [
 *       {
 *         matchType: "high_confidence",
 *         matchedClassUri: "https://schema.org/Customer",
 *         matchedOntologyId: "schema-org-core",
 *         similarity: 0.92,
 *         sourceColumn: "customer_id",
 *         sourceTable: "orders"
 *       }
 *     ],
 *     novelClassesCreated: 7,
 *     tablesProcessed: 12
 *   },
 *   status: "completed"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetInductionJobCommand extends $Command
  .classBuilder<
    GetInductionJobCommandInput,
    GetInductionJobCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetInductionJob", {})
  .n("ControlPlaneServiceClient", "GetInductionJobCommand")
  .sc(GetInductionJob$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetInductionJobInput;
      output: GetInductionJobOutput;
    };
    sdk: {
      input: GetInductionJobCommandInput;
      output: GetInductionJobCommandOutput;
    };
  };
}
