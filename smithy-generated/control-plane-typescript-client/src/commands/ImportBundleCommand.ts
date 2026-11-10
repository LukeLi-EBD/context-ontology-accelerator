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
import type { ImportBundleInput, OntologyBundleImportResult } from "../models/models_0";
import { ImportBundle$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ImportBundleCommand}.
 */
export interface ImportBundleCommandInput extends ImportBundleInput {}
/**
 * @public
 *
 * The output of {@link ImportBundleCommand}.
 */
export interface ImportBundleCommandOutput extends OntologyBundleImportResult, __MetadataBearer {}

/**
 * Restore a bundle into a non-production database.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ImportBundleCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ImportBundleCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ImportBundleInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   bundleRef: "STRING_VALUE", // required
 *   database: "STRING_VALUE",
 *   replace: true || false,
 *   keepDbOnFailure: true || false,
 *   actor: "STRING_VALUE",
 * };
 * const command = new ImportBundleCommand(input);
 * const response = await client.send(command);
 * // { // OntologyBundleImportResult
 * //   ok: true || false,
 * //   database: "STRING_VALUE",
 * //   bundle: "STRING_VALUE",
 * //   tbox: { // BundleTboxRestored
 * //     versionId: "STRING_VALUE",
 * //     contentHash: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //   },
 * //   tboxPointer: { // OntologyPointer
 * //     name: "STRING_VALUE",
 * //     versionId: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE",
 * //     contentHash: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     updatedAt: "STRING_VALUE",
 * //   },
 * //   aboxGraph: "STRING_VALUE",
 * //   checks: [ // BundleCheckList
 * //     { // BundleCheck
 * //       name: "STRING_VALUE", // required
 * //       exported: "DOCUMENT_VALUE",
 * //       imported: "DOCUMENT_VALUE",
 * //       ok: true || false, // required
 * //       detail: "STRING_VALUE",
 * //     },
 * //   ],
 * //   ledger: { // BundleLedger
 * //     events: Number("int"),
 * //     facts: Number("int"),
 * //     chain: true || false,
 * //   },
 * //   blobs: { // BundleBlobs
 * //     included: true || false,
 * //     count: Number("int"),
 * //     bytes: Number("long"),
 * //     written: Number("int"),
 * //     existing: Number("int"),
 * //   },
 * //   counts: "DOCUMENT_VALUE",
 * //   failedStep: "STRING_VALUE",
 * //   error: "STRING_VALUE",
 * //   providerCode: "STRING_VALUE",
 * //   actor: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ImportBundleCommandInput - {@link ImportBundleCommandInput}
 * @returns {@link ImportBundleCommandOutput}
 * @see {@link ImportBundleCommandInput} for command's `input` shape.
 * @see {@link ImportBundleCommandOutput} for command's `response` shape.
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
 * @example Restore a bundle into a test database
 * ```javascript
 * //
 * const input = {
 *   actor: "operator",
 *   bundleRef: "/data/bundles/release-2026-11",
 *   database: "platform_restore_test",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   replace: false
 * };
 * const command = new ImportBundleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   bundle: "/data/bundles/release-2026-11",
 *   database: "platform_restore_test",
 *   ledger: {
 *     chain: true,
 *     events: 41,
 *     facts: 1280
 *   },
 *   ok: true,
 *   tbox: {
 *     graph: "urn:platform:graph:tbox:1a2b3c4d",
 *     versionId: "ont-1a2b3c4d5e6f"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ImportBundleCommand extends $Command
  .classBuilder<
    ImportBundleCommandInput,
    ImportBundleCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ImportBundle", {})
  .n("ControlPlaneServiceClient", "ImportBundleCommand")
  .sc(ImportBundle$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ImportBundleInput;
      output: OntologyBundleImportResult;
    };
    sdk: {
      input: ImportBundleCommandInput;
      output: ImportBundleCommandOutput;
    };
  };
}
