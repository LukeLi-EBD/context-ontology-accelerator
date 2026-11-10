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
import type { InspectOntologyBundleInput, OntologyBundleInspectResult } from "../models/models_0";
import { InspectOntologyBundle$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link InspectOntologyBundleCommand}.
 */
export interface InspectOntologyBundleCommandInput extends InspectOntologyBundleInput {}
/**
 * @public
 *
 * The output of {@link InspectOntologyBundleCommand}.
 */
export interface InspectOntologyBundleCommandOutput extends OntologyBundleInspectResult, __MetadataBearer {}

/**
 * Inspect a bundle's manifest without restoring it.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, InspectOntologyBundleCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, InspectOntologyBundleCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // InspectOntologyBundleInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   bundleRef: "STRING_VALUE", // required
 * };
 * const command = new InspectOntologyBundleCommand(input);
 * const response = await client.send(command);
 * // { // OntologyBundleInspectResult
 * //   ok: true || false, // required
 * //   path: "STRING_VALUE", // required
 * //   tag: "STRING_VALUE",
 * //   totals: { // BundleTotals
 * //     "<keys>": "DOCUMENT_VALUE",
 * //   },
 * //   tbox: "DOCUMENT_VALUE",
 * //   files: Number("int"),
 * // };
 *
 * ```
 *
 * @param InspectOntologyBundleCommandInput - {@link InspectOntologyBundleCommandInput}
 * @returns {@link InspectOntologyBundleCommandOutput}
 * @see {@link InspectOntologyBundleCommandInput} for command's `input` shape.
 * @see {@link InspectOntologyBundleCommandOutput} for command's `response` shape.
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
 * @example Inspect a bundle on disk
 * ```javascript
 * //
 * const input = {
 *   bundleRef: "/data/bundles/release-2026-11",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core"
 * };
 * const command = new InspectOntologyBundleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   files: 42,
 *   ok: true,
 *   path: "/data/bundles/release-2026-11",
 *   tag: "release-2026-11",
 *   totals: {
 *     documents: 12,
 *     triples: 4200
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class InspectOntologyBundleCommand extends $Command
  .classBuilder<
    InspectOntologyBundleCommandInput,
    InspectOntologyBundleCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "InspectOntologyBundle", {})
  .n("ControlPlaneServiceClient", "InspectOntologyBundleCommand")
  .sc(InspectOntologyBundle$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: InspectOntologyBundleInput;
      output: OntologyBundleInspectResult;
    };
    sdk: {
      input: InspectOntologyBundleCommandInput;
      output: InspectOntologyBundleCommandOutput;
    };
  };
}
