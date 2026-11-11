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
import type { ExportOntologyVersionInput, ExportOntologyVersionOutput } from "../models/models_1";
import { ExportOntologyVersion$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ExportOntologyVersionCommand}.
 */
export interface ExportOntologyVersionCommandInput extends ExportOntologyVersionInput {}
/**
 * @public
 *
 * The output of {@link ExportOntologyVersionCommand}.
 */
export interface ExportOntologyVersionCommandOutput extends ExportOntologyVersionOutput, __MetadataBearer {}

/**
 * Export one version as Turtle or N-Quads text.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ExportOntologyVersionCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ExportOntologyVersionCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ExportOntologyVersionInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   versionId: "STRING_VALUE", // required
 *   format: "turtle" || "nquads",
 * };
 * const command = new ExportOntologyVersionCommand(input);
 * const response = await client.send(command);
 * // { // ExportOntologyVersionOutput
 * //   content: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param ExportOntologyVersionCommandInput - {@link ExportOntologyVersionCommandInput}
 * @returns {@link ExportOntologyVersionCommandOutput}
 * @see {@link ExportOntologyVersionCommandInput} for command's `input` shape.
 * @see {@link ExportOntologyVersionCommandOutput} for command's `response` shape.
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
 * @example Export a version as Turtle
 * ```javascript
 * //
 * const input = {
 *   format: "turtle",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   versionId: "ont-1a2b3c4d5e6f"
 * };
 * const command = new ExportOntologyVersionCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   content: "@prefix owl: <http://www.w3.org/2002/07/owl#> .
 * <https://example.com/ontology/core#Invoice> a owl:Class .
 * "
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ExportOntologyVersionCommand extends $Command
  .classBuilder<
    ExportOntologyVersionCommandInput,
    ExportOntologyVersionCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ExportOntologyVersion", {})
  .n("ControlPlaneServiceClient", "ExportOntologyVersionCommand")
  .sc(ExportOntologyVersion$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ExportOntologyVersionInput;
      output: ExportOntologyVersionOutput;
    };
    sdk: {
      input: ExportOntologyVersionCommandInput;
      output: ExportOntologyVersionCommandOutput;
    };
  };
}
