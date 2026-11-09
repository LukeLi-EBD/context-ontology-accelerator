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
import type { GetInferConstraintsJobInput, GetInferConstraintsJobOutput } from "../models/models_0";
import { GetInferConstraintsJob$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetInferConstraintsJobCommand}.
 */
export interface GetInferConstraintsJobCommandInput extends GetInferConstraintsJobInput {}
/**
 * @public
 *
 * The output of {@link GetInferConstraintsJobCommand}.
 */
export interface GetInferConstraintsJobCommandOutput extends GetInferConstraintsJobOutput, __MetadataBearer {}

/**
 * Poll an async constraint-inference job. Status is pending | running |
 * completed | failed; inferred_constraints is present once completed.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetInferConstraintsJobCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetInferConstraintsJobCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetInferConstraintsJobInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 * };
 * const command = new GetInferConstraintsJobCommand(input);
 * const response = await client.send(command);
 * // { // GetInferConstraintsJobOutput
 * //   jobId: "STRING_VALUE", // required
 * //   proposalId: "STRING_VALUE", // required
 * //   status: "STRING_VALUE", // required
 * //   error: "STRING_VALUE",
 * //   inferred_constraints: "DOCUMENT_VALUE",
 * // };
 *
 * ```
 *
 * @param GetInferConstraintsJobCommandInput - {@link GetInferConstraintsJobCommandInput}
 * @returns {@link GetInferConstraintsJobCommandOutput}
 * @see {@link GetInferConstraintsJobCommandInput} for command's `input` shape.
 * @see {@link GetInferConstraintsJobCommandOutput} for command's `response` shape.
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
 * @example Poll a completed constraint-inference job
 * ```javascript
 * //
 * const input = {
 *   jobId: "b4d7e1a2-6c3f-4e9b-8a2d-5f0c7b1e3d9a",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new GetInferConstraintsJobCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   inferred_constraints: {
 *     classes: [
 *       {
 *         properties: [
 *           {
 *             datatype: "decimal",
 *             minCount: 1,
 *             path: "orderTotal"
 *           }
 *         ],
 *         uri: "https://ontology.example.com/sales/Order"
 *       }
 *     ]
 *   },
 *   jobId: "b4d7e1a2-6c3f-4e9b-8a2d-5f0c7b1e3d9a",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   status: "completed"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetInferConstraintsJobCommand extends $Command
  .classBuilder<
    GetInferConstraintsJobCommandInput,
    GetInferConstraintsJobCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetInferConstraintsJob", {})
  .n("ControlPlaneServiceClient", "GetInferConstraintsJobCommand")
  .sc(GetInferConstraintsJob$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetInferConstraintsJobInput;
      output: GetInferConstraintsJobOutput;
    };
    sdk: {
      input: GetInferConstraintsJobCommandInput;
      output: GetInferConstraintsJobCommandOutput;
    };
  };
}
