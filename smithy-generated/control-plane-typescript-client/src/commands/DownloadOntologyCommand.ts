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
import type { DownloadOntologyInput, DownloadOntologyOutput } from "../models/models_0";
import { DownloadOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DownloadOntologyCommand}.
 */
export interface DownloadOntologyCommandInput extends DownloadOntologyInput {}
/**
 * @public
 *
 * The output of {@link DownloadOntologyCommand}.
 */
export interface DownloadOntologyCommandOutput extends DownloadOntologyOutput, __MetadataBearer {}

/**
 * Download an ontology as Turtle.
 *
 * Returns 404 when the ontology does not exist or its graph holds no triples
 * and no cached file is available; nothing is written to the artifacts bucket
 * in that case.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, DownloadOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, DownloadOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // DownloadOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 * };
 * const command = new DownloadOntologyCommand(input);
 * const response = await client.send(command);
 * // { // DownloadOntologyOutput
 * //   downloadUrl: "STRING_VALUE", // required
 * //   expiresInSeconds: Number("int"),
 * // };
 *
 * ```
 *
 * @param DownloadOntologyCommandInput - {@link DownloadOntologyCommandInput}
 * @returns {@link DownloadOntologyCommandOutput}
 * @see {@link DownloadOntologyCommandInput} for command's `input` shape.
 * @see {@link DownloadOntologyCommandOutput} for command's `response` shape.
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
 * @example Download an ontology as Turtle
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "sales-crm"
 * };
 * const command = new DownloadOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   downloadUrl: "https://coa-artifacts.s3.amazonaws.com/downloads/sales-analytics/sales-crm.ttl?X-Amz-Signature=abc123",
 *   expiresInSeconds: 3600
 * }
 * *\/
 * ```
 *
 * @public
 */
export class DownloadOntologyCommand extends $Command
  .classBuilder<
    DownloadOntologyCommandInput,
    DownloadOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "DownloadOntology", {})
  .n("ControlPlaneServiceClient", "DownloadOntologyCommand")
  .sc(DownloadOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DownloadOntologyInput;
      output: DownloadOntologyOutput;
    };
    sdk: {
      input: DownloadOntologyCommandInput;
      output: DownloadOntologyCommandOutput;
    };
  };
}
