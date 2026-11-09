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
import type { GetOntologyUploadUrlInput, GetOntologyUploadUrlOutput } from "../models/models_0";
import { GetOntologyUploadUrl$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologyUploadUrlCommand}.
 */
export interface GetOntologyUploadUrlCommandInput extends GetOntologyUploadUrlInput {}
/**
 * @public
 *
 * The output of {@link GetOntologyUploadUrlCommand}.
 */
export interface GetOntologyUploadUrlCommandOutput extends GetOntologyUploadUrlOutput, __MetadataBearer {}

/**
 * Generate a presigned S3 URL for ontology file upload.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologyUploadUrlCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologyUploadUrlCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologyUploadUrlInput
 *   namespaceId: "STRING_VALUE", // required
 *   filename: "STRING_VALUE", // required
 *   contentType: "STRING_VALUE",
 *   ontologyId: "STRING_VALUE",
 *   title: "STRING_VALUE",
 * };
 * const command = new GetOntologyUploadUrlCommand(input);
 * const response = await client.send(command);
 * // { // GetOntologyUploadUrlOutput
 * //   uploadUrl: "STRING_VALUE", // required
 * //   s3Key: "STRING_VALUE", // required
 * //   ontologyId: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param GetOntologyUploadUrlCommandInput - {@link GetOntologyUploadUrlCommandInput}
 * @returns {@link GetOntologyUploadUrlCommandOutput}
 * @see {@link GetOntologyUploadUrlCommandInput} for command's `input` shape.
 * @see {@link GetOntologyUploadUrlCommandOutput} for command's `response` shape.
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
 * @example Get a presigned upload URL for an ontology file
 * ```javascript
 * //
 * const input = {
 *   contentType: "text/turtle",
 *   filename: "sales-crm.ttl",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "sales-crm",
 *   title: "Sales CRM"
 * };
 * const command = new GetOntologyUploadUrlCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   ontologyId: "sales-crm",
 *   s3Key: "uploads/sales-analytics/sales-crm.ttl",
 *   uploadUrl: "https://coa-uploads.s3.amazonaws.com/sales-analytics/sales-crm.ttl?X-Amz-Signature=abc123"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologyUploadUrlCommand extends $Command
  .classBuilder<
    GetOntologyUploadUrlCommandInput,
    GetOntologyUploadUrlCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntologyUploadUrl", {})
  .n("ControlPlaneServiceClient", "GetOntologyUploadUrlCommand")
  .sc(GetOntologyUploadUrl$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologyUploadUrlInput;
      output: GetOntologyUploadUrlOutput;
    };
    sdk: {
      input: GetOntologyUploadUrlCommandInput;
      output: GetOntologyUploadUrlCommandOutput;
    };
  };
}
