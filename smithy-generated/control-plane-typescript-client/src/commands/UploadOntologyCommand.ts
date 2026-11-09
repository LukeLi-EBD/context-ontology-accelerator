// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { BlobPayloadInputTypes, MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  ControlPlaneServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../ControlPlaneServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { UploadOntologyInput, UploadOntologyOutput } from "../models/models_0";
import { UploadOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 */
export type UploadOntologyCommandInputType = Omit<UploadOntologyInput, "body"> & {
  body: BlobPayloadInputTypes;
};

/**
 * @public
 *
 * The input for {@link UploadOntologyCommand}.
 */
export interface UploadOntologyCommandInput extends UploadOntologyCommandInputType {}
/**
 * @public
 *
 * The output of {@link UploadOntologyCommand}.
 */
export interface UploadOntologyCommandOutput extends UploadOntologyOutput, __MetadataBearer {}

/**
 * Upload an ontology file (Turtle, RDF/XML, or JSON-LD).
 *
 * Not served: the API answers 501 for this path. Uploads go through
 * GetOntologyUploadUrl + IngestOntologyFromS3, which take a `clientToken`;
 * this operation therefore has none.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, UploadOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, UploadOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // UploadOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   body: new Uint8Array(), // e.g. Buffer.from("") or new TextEncoder().encode("")   // required
 * };
 * const command = new UploadOntologyCommand(input);
 * const response = await client.send(command);
 * // { // UploadOntologyOutput
 * //   result: "DOCUMENT_VALUE", // required
 * // };
 *
 * ```
 *
 * @param UploadOntologyCommandInput - {@link UploadOntologyCommandInput}
 * @returns {@link UploadOntologyCommandOutput}
 * @see {@link UploadOntologyCommandInput} for command's `input` shape.
 * @see {@link UploadOntologyCommandOutput} for command's `response` shape.
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
 * @example Upload a Turtle ontology file
 * ```javascript
 * //
 * const input = {
 *   body: "QHByZWZpeCBleDogPGh0dHA6Ly9leGFtcGxlLmNvbS9vbnRvIz4gLgpleDpDdXN0b21lciBhIG93bDpDbGFzcyAuCg==",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "sales-crm"
 * };
 * const command = new UploadOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   result: {
 *     classCount: 12,
 *     ontologyId: "sales-crm",
 *     status: "uploaded"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class UploadOntologyCommand extends $Command
  .classBuilder<
    UploadOntologyCommandInput,
    UploadOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "UploadOntology", {})
  .n("ControlPlaneServiceClient", "UploadOntologyCommand")
  .sc(UploadOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: UploadOntologyInput;
      output: UploadOntologyOutput;
    };
    sdk: {
      input: UploadOntologyCommandInput;
      output: UploadOntologyCommandOutput;
    };
  };
}
