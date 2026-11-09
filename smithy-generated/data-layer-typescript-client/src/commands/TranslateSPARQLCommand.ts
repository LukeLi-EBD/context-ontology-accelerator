// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  DataLayerServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../DataLayerServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { TranslateSPARQLInput, TranslateSPARQLOutput } from "../models/models_0";
import { TranslateSPARQL$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link TranslateSPARQLCommand}.
 */
export interface TranslateSPARQLCommandInput extends TranslateSPARQLInput {}
/**
 * @public
 *
 * The output of {@link TranslateSPARQLCommand}.
 */
export interface TranslateSPARQLCommandOutput extends TranslateSPARQLOutput, __MetadataBearer {}

/**
 * Translate a natural-language question into SPARQL against the namespace's
 * ontology without executing it. Useful for previewing or debugging the query
 * the resolver would run.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, TranslateSPARQLCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, TranslateSPARQLCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // TranslateSPARQLInput
 *   namespaceId: "STRING_VALUE", // required
 *   query: "STRING_VALUE", // required
 * };
 * const command = new TranslateSPARQLCommand(input);
 * const response = await client.send(command);
 * // { // TranslateSPARQLOutput
 * //   sparqlQuery: "STRING_VALUE", // required
 * //   confidence: { // ConfidenceScore
 * //     score: Number("float"), // required
 * //     rationale: "STRING_VALUE",
 * //   },
 * //   trace: [ // TraceStepList // required
 * //     { // TraceStep
 * //       step: "STRING_VALUE", // required
 * //       status: "STRING_VALUE", // required
 * //       durationMs: Number("long"),
 * //       detail: "STRING_VALUE",
 * //       toolUsed: "STRING_VALUE",
 * //       parallelGroup: "STRING_VALUE",
 * //       wallMs: Number("long"),
 * //       conformanceWarnings: [ // ConformanceWarningList
 * //         { // ConformanceWarning
 * //           row: Number("int"), // required
 * //           shape: "STRING_VALUE", // required
 * //           message: "STRING_VALUE", // required
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   ontologyVersion: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param TranslateSPARQLCommandInput - {@link TranslateSPARQLCommandInput}
 * @returns {@link TranslateSPARQLCommandOutput}
 * @see {@link TranslateSPARQLCommandInput} for command's `input` shape.
 * @see {@link TranslateSPARQLCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NamespaceNotFoundError} (client fault)
 *  Returned with HTTP 404 when the target namespace does not exist or is not
 * visible to the caller.
 *
 * @throws {@link OntologyNotPublishedError} (client fault)
 *  Returned with HTTP 409 when the namespace has no published ontology, so the
 * query cannot be resolved against a schema yet.
 *
 * @throws {@link QueryTranslationError} (client fault)
 *  Returned with HTTP 400 when a natural-language question cannot be translated
 * into an executable query against the ontology.
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
 *
 * @throws {@link RateLimitExceededError} (client fault)
 *  Returned with HTTP 429 when the caller exceeds the request rate limit;
 * `retryAfterSeconds` indicates how long to wait before retrying.
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
 * @throws {@link DataLayerServiceServiceException}
 * <p>Base exception class for all service exceptions from DataLayerService service.</p>
 *
 *
 * @example Preview the SPARQL for a question
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   query: "List all customers in the enterprise segment"
 * };
 * const command = new TranslateSPARQLCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   confidence: {
 *     rationale: "Class and property matched from ontology",
 *     score: 0.88
 *   },
 *   ontologyVersion: "2025-09-01",
 *   sparqlQuery: `SELECT ?customer WHERE { ?customer a :Customer ; :segment "enterprise" }`,
 *   trace: [
 *     {
 *       durationMs: 310,
 *       status: "ok",
 *       step: "nl-to-sparql"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class TranslateSPARQLCommand extends $Command
  .classBuilder<
    TranslateSPARQLCommandInput,
    TranslateSPARQLCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "TranslateSPARQL", {})
  .n("DataLayerServiceClient", "TranslateSPARQLCommand")
  .sc(TranslateSPARQL$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: TranslateSPARQLInput;
      output: TranslateSPARQLOutput;
    };
    sdk: {
      input: TranslateSPARQLCommandInput;
      output: TranslateSPARQLCommandOutput;
    };
  };
}
