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
import type { OntologyValidationJob, StartOntologyValidationInput } from "../models/models_1";
import { StartOntologyValidation$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link StartOntologyValidationCommand}.
 */
export interface StartOntologyValidationCommandInput extends StartOntologyValidationInput {}
/**
 * @public
 *
 * The output of {@link StartOntologyValidationCommand}.
 */
export interface StartOntologyValidationCommandOutput extends OntologyValidationJob, __MetadataBearer {}

/**
 * Start an asynchronous multi-tier validation of one ontology.
 *
 * Returns as soon as the job is queued (HTTP 202); poll
 * `GetOntologyValidationJob` with the returned `jobId`. The ontology is read
 * from the catalog by id unless `ontologyTurtle` supplies it inline.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, StartOntologyValidationCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, StartOntologyValidationCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // StartOntologyValidationInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   ontologyTurtle: "STRING_VALUE",
 *   tiers: [ // OntologyValidationTierList
 *     "tier1_blocking" || "tier2_scoring" || "tier3_review",
 *   ],
 *   shaclShapesTurtle: "STRING_VALUE",
 *   competencyQuestions: [ // OntologyValidationQuestionList
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new StartOntologyValidationCommand(input);
 * const response = await client.send(command);
 * // { // OntologyValidationJob
 * //   jobId: "STRING_VALUE", // required
 * //   status: "pending" || "running" || "completed" || "failed", // required
 * //   createdAt: "STRING_VALUE", // required
 * //   report: { // OntologyValidationReport
 * //     jobId: "STRING_VALUE", // required
 * //     ontologyId: "STRING_VALUE",
 * //     passed: true || false, // required
 * //     findings: [ // OntologyValidationFindingList // required
 * //       { // OntologyValidationFinding
 * //         validator: "STRING_VALUE", // required
 * //         tier: "tier1_blocking" || "tier2_scoring" || "tier3_review", // required
 * //         severity: "error" || "warning" || "info", // required
 * //         code: "STRING_VALUE", // required
 * //         message: "STRING_VALUE", // required
 * //         subject: "STRING_VALUE",
 * //         details: "DOCUMENT_VALUE",
 * //       },
 * //     ],
 * //     metrics: { // OntologyValidationMetrics
 * //       classCount: Number("int"),
 * //       objectPropertyCount: Number("int"),
 * //       datatypePropertyCount: Number("int"),
 * //       relationshipRichness: Number("double"),
 * //       attributeRichness: Number("double"),
 * //       inheritanceRichness: Number("double"),
 * //       maxDepth: Number("int"),
 * //       connectedComponents: Number("int"),
 * //     },
 * //     tiersRun: [ // OntologyValidationTierList // required
 * //       "tier1_blocking" || "tier2_scoring" || "tier3_review",
 * //     ],
 * //     createdAt: "STRING_VALUE", // required
 * //   },
 * //   error: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param StartOntologyValidationCommandInput - {@link StartOntologyValidationCommandInput}
 * @returns {@link StartOntologyValidationCommandOutput}
 * @see {@link StartOntologyValidationCommandInput} for command's `input` shape.
 * @see {@link StartOntologyValidationCommandOutput} for command's `response` shape.
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
 * @example Queue a three-tier validation of a catalog ontology
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "urn:acme:ontology:supply-chain"
 * };
 * const command = new StartOntologyValidationCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   createdAt: "2026-11-10T09:12:44Z",
 *   jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d",
 *   status: "pending"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class StartOntologyValidationCommand extends $Command
  .classBuilder<
    StartOntologyValidationCommandInput,
    StartOntologyValidationCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "StartOntologyValidation", {})
  .n("ControlPlaneServiceClient", "StartOntologyValidationCommand")
  .sc(StartOntologyValidation$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: StartOntologyValidationInput;
      output: OntologyValidationJob;
    };
    sdk: {
      input: StartOntologyValidationCommandInput;
      output: StartOntologyValidationCommandOutput;
    };
  };
}
