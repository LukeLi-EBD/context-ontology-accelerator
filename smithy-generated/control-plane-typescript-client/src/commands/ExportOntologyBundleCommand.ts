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
import type { ExportOntologyBundleInput, OntologyBundleExportResult } from "../models/models_0";
import { ExportOntologyBundle$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ExportOntologyBundleCommand}.
 */
export interface ExportOntologyBundleCommandInput extends ExportOntologyBundleInput {}
/**
 * @public
 *
 * The output of {@link ExportOntologyBundleCommand}.
 */
export interface ExportOntologyBundleCommandOutput extends OntologyBundleExportResult, __MetadataBearer {}

/**
 * Export a deployment snapshot into a bundle directory.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ExportOntologyBundleCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ExportOntologyBundleCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ExportOntologyBundleInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   out: "STRING_VALUE",
 *   tag: "STRING_VALUE",
 *   includeBlobs: true || false,
 *   actor: "STRING_VALUE",
 * };
 * const command = new ExportOntologyBundleCommand(input);
 * const response = await client.send(command);
 * // { // OntologyBundleExportResult
 * //   ok: true || false, // required
 * //   bundleDir: "STRING_VALUE", // required
 * //   tag: "STRING_VALUE", // required
 * //   schemaVersion: Number("int"),
 * //   generatedAt: "STRING_VALUE",
 * //   tbox: "DOCUMENT_VALUE",
 * //   totals: { // BundleTotals
 * //     "<keys>": "DOCUMENT_VALUE",
 * //   },
 * //   bytes: Number("long"),
 * //   files: Number("int"),
 * //   actor: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ExportOntologyBundleCommandInput - {@link ExportOntologyBundleCommandInput}
 * @returns {@link ExportOntologyBundleCommandOutput}
 * @see {@link ExportOntologyBundleCommandInput} for command's `input` shape.
 * @see {@link ExportOntologyBundleCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Export a bundle with blobs
 * ```javascript
 * //
 * const input = {
 *   includeBlobs: true,
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   tag: "release-2026-11"
 * };
 * const command = new ExportOntologyBundleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   bundleDir: "/data/bundles/release-2026-11",
 *   bytes: 1048576,
 *   files: 42,
 *   ok: true,
 *   schemaVersion: 3,
 *   tag: "release-2026-11"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ExportOntologyBundleCommand extends $Command
  .classBuilder<
    ExportOntologyBundleCommandInput,
    ExportOntologyBundleCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ExportOntologyBundle", {})
  .n("ControlPlaneServiceClient", "ExportOntologyBundleCommand")
  .sc(ExportOntologyBundle$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ExportOntologyBundleInput;
      output: OntologyBundleExportResult;
    };
    sdk: {
      input: ExportOntologyBundleCommandInput;
      output: ExportOntologyBundleCommandOutput;
    };
  };
}
