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
import type { GetIngestStatusInput, GetIngestStatusOutput } from "../models/models_0";
import { GetIngestStatus$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetIngestStatusCommand}.
 */
export interface GetIngestStatusCommandInput extends GetIngestStatusInput {}
/**
 * @public
 *
 * The output of {@link GetIngestStatusCommand}.
 */
export interface GetIngestStatusCommandOutput extends GetIngestStatusOutput, __MetadataBearer {}

/**
 * Poll ingest job status.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetIngestStatusCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetIngestStatusCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetIngestStatusInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   jobId: "STRING_VALUE", // required
 * };
 * const command = new GetIngestStatusCommand(input);
 * const response = await client.send(command);
 * // { // GetIngestStatusOutput
 * //   result: { // IngestJob
 * //     jobId: "STRING_VALUE", // required
 * //     ontologyId: "STRING_VALUE", // required
 * //     status: "pending" || "running" || "embeddings_sync" || "completed" || "failed", // required
 * //     error: "STRING_VALUE",
 * //     result: { // IngestJobResult
 * //       ontologyId: "STRING_VALUE",
 * //       classCount: Number("int"),
 * //       embeddingCount: Number("int"),
 * //     },
 * //   },
 * // };
 *
 * ```
 *
 * @param GetIngestStatusCommandInput - {@link GetIngestStatusCommandInput}
 * @returns {@link GetIngestStatusCommandOutput}
 * @see {@link GetIngestStatusCommandInput} for command's `input` shape.
 * @see {@link GetIngestStatusCommandOutput} for command's `response` shape.
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
 * @example Poll a completed ingest job
 * ```javascript
 * //
 * const input = {
 *   jobId: "01J9ZQ8XN4T7VBR6C2K9YHMED0",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "sales-crm"
 * };
 * const command = new GetIngestStatusCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   result: {
 *     jobId: "01J9ZQ8XN4T7VBR6C2K9YHMED0",
 *     ontologyId: "sales-crm",
 *     result: {
 *       classCount: 12,
 *       embeddingCount: 46,
 *       ontologyId: "sales-crm"
 *     },
 *     status: "completed"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetIngestStatusCommand extends $Command
  .classBuilder<
    GetIngestStatusCommandInput,
    GetIngestStatusCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetIngestStatus", {})
  .n("ControlPlaneServiceClient", "GetIngestStatusCommand")
  .sc(GetIngestStatus$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetIngestStatusInput;
      output: GetIngestStatusOutput;
    };
    sdk: {
      input: GetIngestStatusCommandInput;
      output: GetIngestStatusCommandOutput;
    };
  };
}
