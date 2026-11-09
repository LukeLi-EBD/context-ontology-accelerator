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
import type { GetProposalUploadUrlsInput, GetProposalUploadUrlsOutput } from "../models/models_0";
import { GetProposalUploadUrls$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetProposalUploadUrlsCommand}.
 */
export interface GetProposalUploadUrlsCommandInput extends GetProposalUploadUrlsInput {}
/**
 * @public
 *
 * The output of {@link GetProposalUploadUrlsCommand}.
 */
export interface GetProposalUploadUrlsCommandOutput extends GetProposalUploadUrlsOutput, __MetadataBearer {}

/**
 * Get create-only presigned S3 PUT URLs for a large revised proposal Turtle.
 * Each direct PUT must send `If-None-Match: *`, which is a signed S3 header,
 * and may create its artifact key only once. After every requested upload
 * succeeds, call UpdateProposal with `ontologyUploaded` / `r2rmlUploaded` set.
 * A 409, 412, or ambiguous network outcome requires requesting a fresh
 * revision and re-uploading every changed artifact; callers must not reuse the
 * prior URLs or assume that an uncertain write succeeded.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetProposalUploadUrlsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetProposalUploadUrlsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetProposalUploadUrlsInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 * };
 * const command = new GetProposalUploadUrlsCommand(input);
 * const response = await client.send(command);
 * // { // GetProposalUploadUrlsOutput
 * //   revisionId: "STRING_VALUE", // required
 * //   ontologyPutUrl: "STRING_VALUE", // required
 * //   r2rmlPutUrl: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param GetProposalUploadUrlsCommandInput - {@link GetProposalUploadUrlsCommandInput}
 * @returns {@link GetProposalUploadUrlsCommandOutput}
 * @see {@link GetProposalUploadUrlsCommandInput} for command's `input` shape.
 * @see {@link GetProposalUploadUrlsCommandOutput} for command's `response` shape.
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
 * @example Get presigned PUT URLs for a large proposal revision
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new GetProposalUploadUrlsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   ontologyPutUrl: "https://coa-proposals.s3.amazonaws.com/ont-sales-2026/ontology.ttl?X-Amz-Signature=abc123",
 *   r2rmlPutUrl: "https://coa-proposals.s3.amazonaws.com/ont-sales-2026/mappings.ttl?X-Amz-Signature=def456",
 *   revisionId: "d3bc58e9-52a4-43cf-b8b2-44a2f05b43f8"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetProposalUploadUrlsCommand extends $Command
  .classBuilder<
    GetProposalUploadUrlsCommandInput,
    GetProposalUploadUrlsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetProposalUploadUrls", {})
  .n("ControlPlaneServiceClient", "GetProposalUploadUrlsCommand")
  .sc(GetProposalUploadUrls$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetProposalUploadUrlsInput;
      output: GetProposalUploadUrlsOutput;
    };
    sdk: {
      input: GetProposalUploadUrlsCommandInput;
      output: GetProposalUploadUrlsCommandOutput;
    };
  };
}
