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
import type { InferConstraintsInput, InferConstraintsOutput } from "../models/models_0";
import { InferConstraints$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link InferConstraintsCommand}.
 */
export interface InferConstraintsCommandInput extends InferConstraintsInput {}
/**
 * @public
 *
 * The output of {@link InferConstraintsCommand}.
 */
export interface InferConstraintsCommandOutput extends InferConstraintsOutput, __MetadataBearer {}

/**
 * Start LLM inference of semantic constraints from the proposal's ontology.
 * Runs asynchronously (the LLM call can exceed the API-GW 29s timeout);
 * returns 202 + a job handle. Poll GetInferConstraintsJob for the result.
 * Each call starts a new job; send a `clientToken` to make a retry safe.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, InferConstraintsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, InferConstraintsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // InferConstraintsInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new InferConstraintsCommand(input);
 * const response = await client.send(command);
 * // { // InferConstraintsOutput
 * //   jobId: "STRING_VALUE", // required
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param InferConstraintsCommandInput - {@link InferConstraintsCommandInput}
 * @returns {@link InferConstraintsCommandOutput}
 * @see {@link InferConstraintsCommandInput} for command's `input` shape.
 * @see {@link InferConstraintsCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Start constraint inference for a proposal
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new InferConstraintsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   jobId: "b4d7e1a2-6c3f-4e9b-8a2d-5f0c7b1e3d9a",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   status: "pending"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class InferConstraintsCommand extends $Command
  .classBuilder<
    InferConstraintsCommandInput,
    InferConstraintsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "InferConstraints", {})
  .n("ControlPlaneServiceClient", "InferConstraintsCommand")
  .sc(InferConstraints$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: InferConstraintsInput;
      output: InferConstraintsOutput;
    };
    sdk: {
      input: InferConstraintsCommandInput;
      output: InferConstraintsCommandOutput;
    };
  };
}
