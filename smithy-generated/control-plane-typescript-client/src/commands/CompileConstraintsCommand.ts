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
import type { CompileConstraintsInput, CompileConstraintsOutput } from "../models/models_0";
import { CompileConstraints$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CompileConstraintsCommand}.
 */
export interface CompileConstraintsCommandInput extends CompileConstraintsInput {}
/**
 * @public
 *
 * The output of {@link CompileConstraintsCommand}.
 */
export interface CompileConstraintsCommandOutput extends CompileConstraintsOutput, __MetadataBearer {}

/**
 * Compile a reviewed ConstraintConfig into SHACL Turtle.
 *
 * Pure computation over the request and the stored proposal; nothing is
 * persisted, so a retry is harmless and there is no `clientToken`.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, CompileConstraintsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, CompileConstraintsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // CompileConstraintsInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   constraint_config: "DOCUMENT_VALUE", // required
 *   custom_turtle: "STRING_VALUE",
 * };
 * const command = new CompileConstraintsCommand(input);
 * const response = await client.send(command);
 * // { // CompileConstraintsOutput
 * //   proposalId: "STRING_VALUE", // required
 * //   shapes_turtle: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param CompileConstraintsCommandInput - {@link CompileConstraintsCommandInput}
 * @returns {@link CompileConstraintsCommandOutput}
 * @see {@link CompileConstraintsCommandInput} for command's `input` shape.
 * @see {@link CompileConstraintsCommandOutput} for command's `response` shape.
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
 * @example Compile a reviewed constraint config into SHACL
 * ```javascript
 * //
 * const input = {
 *   constraint_config: {
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
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new CompileConstraintsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   shapes_turtle: "@prefix sh: <http://www.w3.org/ns/shacl#> .
 * :OrderShape a sh:NodeShape ;
 *     sh:targetClass :Order ."
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CompileConstraintsCommand extends $Command
  .classBuilder<
    CompileConstraintsCommandInput,
    CompileConstraintsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "CompileConstraints", {})
  .n("ControlPlaneServiceClient", "CompileConstraintsCommand")
  .sc(CompileConstraints$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CompileConstraintsInput;
      output: CompileConstraintsOutput;
    };
    sdk: {
      input: CompileConstraintsCommandInput;
      output: CompileConstraintsCommandOutput;
    };
  };
}
