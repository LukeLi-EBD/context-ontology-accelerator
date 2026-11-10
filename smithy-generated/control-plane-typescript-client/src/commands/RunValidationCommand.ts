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
import type { RunValidationInput, RunValidationOutput } from "../models/models_0";
import { RunValidation$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RunValidationCommand}.
 */
export interface RunValidationCommandInput extends RunValidationInput {}
/**
 * @public
 *
 * The output of {@link RunValidationCommand}.
 */
export interface RunValidationCommandOutput extends RunValidationOutput, __MetadataBearer {}

/**
 * Run the read-only quality checks the health board reports.
 *
 * Despite the verb, nothing is written: the operation measures orphan
 * instances, unlabeled classes and SHACL conformance. Checks that cannot
 * run (no shapes, no reasoner) report a null count with a ``detail`` —
 * never a fabricated zero.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RunValidationCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RunValidationCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RunValidationInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new RunValidationCommand(input);
 * const response = await client.send(command);
 * // { // RunValidationOutput
 * //   orphanInstances: { // QualityCount
 * //     count: Number("int"),
 * //     detail: "STRING_VALUE",
 * //   },
 * //   unlabeledClasses: {
 * //     count: Number("int"),
 * //     detail: "STRING_VALUE",
 * //   },
 * //   shacl: { // ShaclReport
 * //     status: "STRING_VALUE", // required
 * //     violations: Number("int"),
 * //     conforms: true || false,
 * //     detail: "STRING_VALUE",
 * //   },
 * //   inferenceFailures: {
 * //     count: Number("int"),
 * //     detail: "STRING_VALUE",
 * //   },
 * //   source: "STRING_VALUE", // required
 * //   sampledAt: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param RunValidationCommandInput - {@link RunValidationCommandInput}
 * @returns {@link RunValidationCommandOutput}
 * @see {@link RunValidationCommandInput} for command's `input` shape.
 * @see {@link RunValidationCommandOutput} for command's `response` shape.
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
 * @example Run the read-only quality checks
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new RunValidationCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   inferenceFailures: {
 *     detail: "no reasoner wired up in this deployment"
 *   },
 *   orphanInstances: {
 *     count: 0,
 *     detail: "instances typed by a declared class with no other edge"
 *   },
 *   sampledAt: "2026-11-10T09:00:00Z",
 *   shacl: {
 *     detail: "no shapes configured (no-shapes)",
 *     status: "skipped"
 *   },
 *   source: "SPARQL over the namespace named graphs; SHACL shapes from the configured shapes file",
 *   unlabeledClasses: {
 *     count: 0,
 *     detail: "declared classes missing rdfs:label and skos:prefLabel"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RunValidationCommand extends $Command
  .classBuilder<
    RunValidationCommandInput,
    RunValidationCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RunValidation", {})
  .n("ControlPlaneServiceClient", "RunValidationCommand")
  .sc(RunValidation$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RunValidationInput;
      output: RunValidationOutput;
    };
    sdk: {
      input: RunValidationCommandInput;
      output: RunValidationCommandOutput;
    };
  };
}
