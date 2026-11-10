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
import type { ImportOntologyInput, OntologyImportResult } from "../models/models_1";
import { ImportOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ImportOntologyCommand}.
 */
export interface ImportOntologyCommandInput extends ImportOntologyInput {}
/**
 * @public
 *
 * The output of {@link ImportOntologyCommand}.
 */
export interface ImportOntologyCommandOutput extends OntologyImportResult, __MetadataBearer {}

/**
 * Register an uploaded ontology as a draft version.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ImportOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ImportOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ImportOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   content: "STRING_VALUE", // required
 *   format: "turtle" || "nt",
 *   changeSummary: "STRING_VALUE",
 *   author: "STRING_VALUE",
 * };
 * const command = new ImportOntologyCommand(input);
 * const response = await client.send(command);
 * // { // OntologyImportResult
 * //   importId: "STRING_VALUE", // required
 * //   versionId: "STRING_VALUE", // required
 * //   targetNamespace: "STRING_VALUE",
 * //   author: "STRING_VALUE",
 * //   changeSummary: "STRING_VALUE",
 * //   format: "STRING_VALUE",
 * //   triples: Number("int"),
 * //   totalTriples: Number("int"),
 * //   classes: Number("int"),
 * //   objectProperties: Number("int"),
 * //   dataProperties: Number("int"),
 * //   importsDeclared: [ // OntologyStringList
 * //     "STRING_VALUE",
 * //   ],
 * //   importsResolved: [ // DocumentList
 * //     "DOCUMENT_VALUE",
 * //   ],
 * //   unresolvedImports: [
 * //     "DOCUMENT_VALUE",
 * //   ],
 * //   shacl: { // OntologyShaclResult
 * //     shapesId: "STRING_VALUE",
 * //     shapesVersion: "STRING_VALUE",
 * //     conforms: true || false,
 * //     violationCount: Number("int"),
 * //     status: "STRING_VALUE",
 * //     engine: "STRING_VALUE",
 * //     error: "STRING_VALUE",
 * //     violations: [
 * //       "DOCUMENT_VALUE",
 * //     ],
 * //   },
 * //   consistency: "DOCUMENT_VALUE",
 * //   usable: true || false,
 * //   reason: "STRING_VALUE",
 * //   usableReasons: [
 * //     "DOCUMENT_VALUE",
 * //   ],
 * //   published: true || false,
 * //   persisted: true || false,
 * //   slice: "STRING_VALUE",
 * //   stagingGraph: "STRING_VALUE",
 * //   sourceSha256: "STRING_VALUE",
 * //   createdAt: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ImportOntologyCommandInput - {@link ImportOntologyCommandInput}
 * @returns {@link ImportOntologyCommandOutput}
 * @see {@link ImportOntologyCommandInput} for command's `input` shape.
 * @see {@link ImportOntologyCommandOutput} for command's `response` shape.
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
 * @example Register a Turtle draft
 * ```javascript
 * //
 * const input = {
 *   changeSummary: "add Invoice class",
 *   content: "@prefix owl: <http://www.w3.org/2002/07/owl#> .
 * <https://example.com/ontology/core#Invoice> a owl:Class .
 * ",
 *   format: "turtle",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core"
 * };
 * const command = new ImportOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   classes: 1,
 *   dataProperties: 0,
 *   format: "turtle",
 *   importId: "imp-1a2b3c4d5e6f",
 *   importsDeclared:   [],
 *   importsResolved:   [],
 *   objectProperties: 0,
 *   persisted: true,
 *   published: false,
 *   targetNamespace: "https://example.com/ontology/core",
 *   totalTriples: 1,
 *   unresolvedImports:   [],
 *   usable: true,
 *   versionId: "ont-draft-9f8e7d6c5b4a"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ImportOntologyCommand extends $Command
  .classBuilder<
    ImportOntologyCommandInput,
    ImportOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ImportOntology", {})
  .n("ControlPlaneServiceClient", "ImportOntologyCommand")
  .sc(ImportOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ImportOntologyInput;
      output: OntologyImportResult;
    };
    sdk: {
      input: ImportOntologyCommandInput;
      output: ImportOntologyCommandOutput;
    };
  };
}
