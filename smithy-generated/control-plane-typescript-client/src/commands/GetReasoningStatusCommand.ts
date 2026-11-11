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
import type { GetReasoningStatusInput, GetReasoningStatusOutput } from "../models/models_0";
import { GetReasoningStatus$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetReasoningStatusCommand}.
 */
export interface GetReasoningStatusCommandInput extends GetReasoningStatusInput {}
/**
 * @public
 *
 * The output of {@link GetReasoningStatusCommand}.
 */
export interface GetReasoningStatusCommandOutput extends GetReasoningStatusOutput, __MetadataBearer {}

/**
 * Report whether an inference engine is wired up and how its last job went.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetReasoningStatusCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetReasoningStatusCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetReasoningStatusInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new GetReasoningStatusCommand(input);
 * const response = await client.send(command);
 * // { // GetReasoningStatusOutput
 * //   available: true || false, // required
 * //   engine: "STRING_VALUE",
 * //   failures: { // QualityCount
 * //     count: Number("int"),
 * //     detail: "STRING_VALUE",
 * //   },
 * //   detail: "STRING_VALUE",
 * //   source: "STRING_VALUE", // required
 * //   sampledAt: "STRING_VALUE", // required
 * //   inferredTriples: Number("int"),
 * //   lastJob: { // ReasoningJobSummary
 * //     jobId: "STRING_VALUE", // required
 * //     state: "STRING_VALUE", // required
 * //     inferred: Number("int"),
 * //     consistent: true || false,
 * //     finishedAt: "STRING_VALUE",
 * //     skipped: true || false,
 * //     stages: { // ReasoningStages
 * //       rdfs: { // ReasoningStage
 * //         triples: Number("int"),
 * //         conforms: true || false,
 * //         violations: Number("int"),
 * //         ms: Number("int"),
 * //       },
 * //       owl: {
 * //         triples: Number("int"),
 * //         conforms: true || false,
 * //         violations: Number("int"),
 * //         ms: Number("int"),
 * //       },
 * //       shacl: {
 * //         triples: Number("int"),
 * //         conforms: true || false,
 * //         violations: Number("int"),
 * //         ms: Number("int"),
 * //       },
 * //     },
 * //   },
 * // };
 *
 * ```
 *
 * @param GetReasoningStatusCommandInput - {@link GetReasoningStatusCommandInput}
 * @returns {@link GetReasoningStatusCommandOutput}
 * @see {@link GetReasoningStatusCommandInput} for command's `input` shape.
 * @see {@link GetReasoningStatusCommandOutput} for command's `response` shape.
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
 * @example No reasoner configured
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetReasoningStatusCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   available: false,
 *   detail: "This deployment does not configure a reasoner; only asserted triples are served.",
 *   failures: {
 *     detail: "inference jobs are not observable from this service"
 *   },
 *   sampledAt: "2026-11-10T09:00:00Z",
 *   source: "ontology-engine capability check"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetReasoningStatusCommand extends $Command
  .classBuilder<
    GetReasoningStatusCommandInput,
    GetReasoningStatusCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetReasoningStatus", {})
  .n("ControlPlaneServiceClient", "GetReasoningStatusCommand")
  .sc(GetReasoningStatus$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetReasoningStatusInput;
      output: GetReasoningStatusOutput;
    };
    sdk: {
      input: GetReasoningStatusCommandInput;
      output: GetReasoningStatusCommandOutput;
    };
  };
}
