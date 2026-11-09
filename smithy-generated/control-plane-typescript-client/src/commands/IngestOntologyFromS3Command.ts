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
import type { IngestOntologyFromS3Input, IngestOntologyFromS3Output } from "../models/models_0";
import { IngestOntologyFromS3$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link IngestOntologyFromS3Command}.
 */
export interface IngestOntologyFromS3CommandInput extends IngestOntologyFromS3Input {}
/**
 * @public
 *
 * The output of {@link IngestOntologyFromS3Command}.
 */
export interface IngestOntologyFromS3CommandOutput extends IngestOntologyFromS3Output, __MetadataBearer {}

/**
 * Ingest an ontology file from S3 (async — returns 202, poll ingest-status).
 *
 * Each call starts a new ingest job; send a `clientToken` to make a retry safe.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, IngestOntologyFromS3Command } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, IngestOntologyFromS3Command } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // IngestOntologyFromS3Input
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   s3Key: "STRING_VALUE", // required
 *   format: "turtle" || "ttl" || "rdf-xml" || "rdf+xml" || "owl-xml" || "xml" || "json-ld" || "jsonld",
 *   title: "STRING_VALUE",
 *   ontologyType: "foundational" || "induced" || "user_created" || "user_uploaded",
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new IngestOntologyFromS3Command(input);
 * const response = await client.send(command);
 * // { // IngestOntologyFromS3Output
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
 * @param IngestOntologyFromS3CommandInput - {@link IngestOntologyFromS3CommandInput}
 * @returns {@link IngestOntologyFromS3CommandOutput}
 * @see {@link IngestOntologyFromS3CommandInput} for command's `input` shape.
 * @see {@link IngestOntologyFromS3CommandOutput} for command's `response` shape.
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
 * @example Kick off an async ingest from S3
 * ```javascript
 * //
 * const input = {
 *   format: "turtle",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "sales-crm",
 *   ontologyType: "induced",
 *   s3Key: "uploads/sales-analytics/sales-crm.ttl",
 *   title: "Sales CRM"
 * };
 * const command = new IngestOntologyFromS3Command(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   result: {
 *     jobId: "01J9ZQ8XN4T7VBR6C2K9YHMED0",
 *     ontologyId: "sales-crm",
 *     status: "pending"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class IngestOntologyFromS3Command extends $Command
  .classBuilder<
    IngestOntologyFromS3CommandInput,
    IngestOntologyFromS3CommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "IngestOntologyFromS3", {})
  .n("ControlPlaneServiceClient", "IngestOntologyFromS3Command")
  .sc(IngestOntologyFromS3$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: IngestOntologyFromS3Input;
      output: IngestOntologyFromS3Output;
    };
    sdk: {
      input: IngestOntologyFromS3CommandInput;
      output: IngestOntologyFromS3CommandOutput;
    };
  };
}
