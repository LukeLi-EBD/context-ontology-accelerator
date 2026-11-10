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
import type { OntologyVerifyResult, VerifyOntologyInput } from "../models/models_1";
import { VerifyOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link VerifyOntologyCommand}.
 */
export interface VerifyOntologyCommandInput extends VerifyOntologyInput {}
/**
 * @public
 *
 * The output of {@link VerifyOntologyCommand}.
 */
export interface VerifyOntologyCommandOutput extends OntologyVerifyResult, __MetadataBearer {}

/**
 * Recompute the lifecycle and PROV hash chains and report broken links.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, VerifyOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, VerifyOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // VerifyOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 * };
 * const command = new VerifyOntologyCommand(input);
 * const response = await client.send(command);
 * // { // OntologyVerifyResult
 * //   ok: true || false, // required
 * //   checked: Number("int"), // required
 * //   error: "STRING_VALUE",
 * //   prov: { // OntologyProvResult
 * //     ok: true || false, // required
 * //     checked: Number("int"), // required
 * //     error: "STRING_VALUE",
 * //     lastHash: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //   },
 * //   separation: { // OntologySeparationResult
 * //     ok: true || false, // required
 * //     provGraph: "STRING_VALUE",
 * //     tboxGraph: "STRING_VALUE",
 * //     provTriples: Number("int"),
 * //     tboxProvTriples: Number("int"),
 * //     provTboxTriples: Number("int"),
 * //     tboxLegacyProvPredicateTriples: Number("int"),
 * //   },
 * // };
 *
 * ```
 *
 * @param VerifyOntologyCommandInput - {@link VerifyOntologyCommandInput}
 * @returns {@link VerifyOntologyCommandOutput}
 * @see {@link VerifyOntologyCommandInput} for command's `input` shape.
 * @see {@link VerifyOntologyCommandOutput} for command's `response` shape.
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
 * @example Verify both audit chains
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core"
 * };
 * const command = new VerifyOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   checked: 41,
 *   ok: true,
 *   prov: {
 *     checked: 12,
 *     graph: "urn:platform:graph:prov",
 *     ok: true
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class VerifyOntologyCommand extends $Command
  .classBuilder<
    VerifyOntologyCommandInput,
    VerifyOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "VerifyOntology", {})
  .n("ControlPlaneServiceClient", "VerifyOntologyCommand")
  .sc(VerifyOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: VerifyOntologyInput;
      output: OntologyVerifyResult;
    };
    sdk: {
      input: VerifyOntologyCommandInput;
      output: VerifyOntologyCommandOutput;
    };
  };
}
