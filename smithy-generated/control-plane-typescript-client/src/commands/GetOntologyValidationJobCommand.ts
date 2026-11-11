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
import type { GetOntologyValidationJobInput, OntologyValidationJob } from "../models/models_1";
import { GetOntologyValidationJob$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologyValidationJobCommand}.
 */
export interface GetOntologyValidationJobCommandInput extends GetOntologyValidationJobInput {}
/**
 * @public
 *
 * The output of {@link GetOntologyValidationJobCommand}.
 */
export interface GetOntologyValidationJobCommandOutput extends OntologyValidationJob, __MetadataBearer {}

/**
 * Read the current state of one validation job.
 *
 * Poll this after `StartOntologyValidation`. Unknown ids, and jobs belonging
 * to another namespace, both answer `NotFoundError` — the two are not
 * distinguished so a caller cannot probe for foreign job ids.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologyValidationJobCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologyValidationJobCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologyValidationJobInput
 *   namespaceId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 * };
 * const command = new GetOntologyValidationJobCommand(input);
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
 * @param GetOntologyValidationJobCommandInput - {@link GetOntologyValidationJobCommandInput}
 * @returns {@link GetOntologyValidationJobCommandOutput}
 * @see {@link GetOntologyValidationJobCommandInput} for command's `input` shape.
 * @see {@link GetOntologyValidationJobCommandOutput} for command's `response` shape.
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
 * @example Read a completed job with two findings
 * ```javascript
 * //
 * const input = {
 *   jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetOntologyValidationJobCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   createdAt: "2026-11-10T09:12:44Z",
 *   jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d",
 *   report: {
 *     createdAt: "2026-11-10T09:12:51Z",
 *     findings: [
 *       {
 *         code: "SHACL_VALIDATION_FAILED",
 *         message: "Property ex:supplier is required but missing on 3 instances.",
 *         severity: "error",
 *         subject: "urn:acme:entity:shipment-42",
 *         tier: "tier1_blocking",
 *         validator: "shacl"
 *       },
 *       {
 *         code: "LOW_RELATIONSHIP_RICHNESS",
 *         message: "Only 0.21 of relations are non-inheritance.",
 *         severity: "warning",
 *         tier: "tier2_scoring",
 *         validator: "structural"
 *       }
 *     ],
 *     jobId: "b7c9e2a1-4d3f-4a6b-9c8d-0e1f2a3b4c5d",
 *     metrics: {
 *       classCount: 42,
 *       connectedComponents: 1,
 *       datatypePropertyCount: 27,
 *       maxDepth: 4,
 *       objectPropertyCount: 18,
 *       relationshipRichness: 0.21
 *     },
 *     ontologyId: "urn:acme:ontology:supply-chain",
 *     passed: false,
 *     tiersRun: [
 *       "tier1_blocking",
 *       "tier2_scoring"
 *     ]
 *   },
 *   status: "completed"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologyValidationJobCommand extends $Command
  .classBuilder<
    GetOntologyValidationJobCommandInput,
    GetOntologyValidationJobCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntologyValidationJob", {})
  .n("ControlPlaneServiceClient", "GetOntologyValidationJobCommand")
  .sc(GetOntologyValidationJob$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologyValidationJobInput;
      output: OntologyValidationJob;
    };
    sdk: {
      input: GetOntologyValidationJobCommandInput;
      output: GetOntologyValidationJobCommandOutput;
    };
  };
}
