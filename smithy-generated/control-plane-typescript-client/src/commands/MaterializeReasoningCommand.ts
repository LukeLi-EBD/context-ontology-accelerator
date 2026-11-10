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
import type { MaterializeReasoningInput, MaterializeReasoningOutput } from "../models/models_0";
import { MaterializeReasoning$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link MaterializeReasoningCommand}.
 */
export interface MaterializeReasoningCommandInput extends MaterializeReasoningInput {}
/**
 * @public
 *
 * The output of {@link MaterializeReasoningCommand}.
 */
export interface MaterializeReasoningCommandOutput extends MaterializeReasoningOutput, __MetadataBearer {}

/**
 * Run inference over the published T-Box plus this namespace's A-Box graphs
 * and replace the inferred graph for the published version.
 *
 * The call is synchronous and can take a minute on a large A-Box. A second
 * concurrent call for the same target answers 409. When the inputs hash the
 * same as the recorded pointer and the target graph still holds exactly that
 * many triples, the run is reported as `skipped` without writing.
 *
 * The reported `inferred` count is what this run added; it is not the size
 * of the inferred graph.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, MaterializeReasoningCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, MaterializeReasoningCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // MaterializeReasoningInput
 *   namespaceId: "STRING_VALUE", // required
 *   profile: "STRING_VALUE",
 *   force: true || false,
 *   aboxGraphs: [ // PlatformGraphIriList
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new MaterializeReasoningCommand(input);
 * const response = await client.send(command);
 * // { // MaterializeReasoningOutput
 * //   jobId: "STRING_VALUE", // required
 * //   mode: "STRING_VALUE", // required
 * //   profile: "STRING_VALUE", // required
 * //   ontologyVersion: "STRING_VALUE", // required
 * //   targetGraph: "STRING_VALUE", // required
 * //   inferred: Number("int"), // required
 * //   skipped: true || false, // required
 * //   consistent: true || false, // required
 * //   inputHash: "STRING_VALUE",
 * //   ms: Number("int"), // required
 * //   stages: { // ReasoningStages
 * //     rdfs: { // ReasoningStage
 * //       triples: Number("int"),
 * //       conforms: true || false,
 * //       violations: Number("int"),
 * //       ms: Number("int"),
 * //     },
 * //     owl: {
 * //       triples: Number("int"),
 * //       conforms: true || false,
 * //       violations: Number("int"),
 * //       ms: Number("int"),
 * //     },
 * //     shacl: {
 * //       triples: Number("int"),
 * //       conforms: true || false,
 * //       violations: Number("int"),
 * //       ms: Number("int"),
 * //     },
 * //   },
 * //   warnings: [ // StringList // required
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param MaterializeReasoningCommandInput - {@link MaterializeReasoningCommandInput}
 * @returns {@link MaterializeReasoningCommandOutput}
 * @see {@link MaterializeReasoningCommandInput} for command's `input` shape.
 * @see {@link MaterializeReasoningCommandOutput} for command's `response` shape.
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
 * @example Materialize with the default profile
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new MaterializeReasoningCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   consistent: true,
 *   inferred: 91052,
 *   inputHash: "7ef8727158b43f4ae92054670a79a28aa8c3199f877d11f0a07679f83b6196de",
 *   jobId: "rsn-1a2b3c4d5e6f",
 *   mode: "materialize",
 *   ms: 72891,
 *   ontologyVersion: "ont-7c6971e77b7d",
 *   profile: "EL",
 *   skipped: false,
 *   stages: {
 *     owl: {
 *       ms: 26234,
 *       triples: 37686
 *     },
 *     rdfs: {
 *       ms: 17342,
 *       triples: 53366
 *     },
 *     shacl: {
 *       conforms: true,
 *       ms: 22484,
 *       violations: 0
 *     }
 *   },
 *   targetGraph: "urn:platform:inferred:ont-7c6971e77b7d",
 *   warnings:   []
 * }
 * *\/
 * ```
 *
 * @public
 */
export class MaterializeReasoningCommand extends $Command
  .classBuilder<
    MaterializeReasoningCommandInput,
    MaterializeReasoningCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "MaterializeReasoning", {})
  .n("ControlPlaneServiceClient", "MaterializeReasoningCommand")
  .sc(MaterializeReasoning$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: MaterializeReasoningInput;
      output: MaterializeReasoningOutput;
    };
    sdk: {
      input: MaterializeReasoningCommandInput;
      output: MaterializeReasoningCommandOutput;
    };
  };
}
