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
import type { RunSparqlInput, RunSparqlOutput } from "../models/models_0";
import { RunSparql$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RunSparqlCommand}.
 */
export interface RunSparqlCommandInput extends RunSparqlInput {}
/**
 * @public
 *
 * The output of {@link RunSparqlCommand}.
 */
export interface RunSparqlCommandOutput extends RunSparqlOutput, __MetadataBearer {}

/**
 * Runs one SPARQL SELECT or ASK in the SPARQL console.
 *
 * The query is confined to the namespace's own graphs: they form the default
 * graph and each stays addressable as a named graph. The statement is refused
 * when it carries `FROM` / `FROM NAMED`, uses `SERVICE` or `LOAD`, names a graph
 * outside the namespace, is not SELECT/ASK, runs longer than 10 seconds, or
 * produces more than 4 MiB. At most 5,000 rows are returned; `truncated` says
 * whether the provider produced more.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, RunSparqlCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, RunSparqlCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // RunSparqlInput
 *   namespaceId: "STRING_VALUE", // required
 *   sparql: "STRING_VALUE", // required
 * };
 * const command = new RunSparqlCommand(input);
 * const response = await client.send(command);
 * // { // RunSparqlOutput
 * //   form: "STRING_VALUE", // required
 * //   answer: true || false,
 * //   variables: [ // SparqlVariableList
 * //     "STRING_VALUE",
 * //   ],
 * //   rows: [ // SparqlRowList
 * //     [ // SparqlRow
 * //       "STRING_VALUE",
 * //     ],
 * //   ],
 * //   rowCount: Number("int"), // required
 * //   returnedRows: Number("int"), // required
 * //   truncated: true || false, // required
 * //   graphCount: Number("int"), // required
 * //   elapsedMs: Number("int"),
 * // };
 *
 * ```
 *
 * @param RunSparqlCommandInput - {@link RunSparqlCommandInput}
 * @returns {@link RunSparqlCommandOutput}
 * @see {@link RunSparqlCommandInput} for command's `input` shape.
 * @see {@link RunSparqlCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link NamespaceNotFoundError} (client fault)
 *  Returned with HTTP 404 when the target namespace does not exist or is not
 * visible to the caller.
 *
 * @throws {@link SparqlBadRequestError} (client fault)
 *  The statement was refused before execution: syntax, form, dataset clause,
 * federation, `LOAD`, length, or a graph outside the namespace.
 *
 * @throws {@link SparqlResultTooLargeError} (client fault)
 *  The result exceeded the 4 MiB response cap.
 *
 * @throws {@link SparqlQuotaExceededError} (client fault)
 *  The caller exceeded the console quota.
 *
 * @throws {@link SparqlProviderError} (server fault)
 *  The provider could not execute the statement.
 *
 * @throws {@link SparqlScopeTooLargeError} (server fault)
 *  The namespace needs more graphs than the console admits.
 *
 * @throws {@link SparqlTimeoutError} (server fault)
 *  The statement exceeded the 10 second limit.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
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
 * @example List five subjects in the namespace
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   sparql: "SELECT ?s WHERE { ?s ?p ?o } LIMIT 5"
 * };
 * const command = new RunSparqlCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   elapsedMs: 37,
 *   form: "SELECT",
 *   graphCount: 2,
 *   returnedRows: 1,
 *   rowCount: 1,
 *   rows: [
 *     [
 *       "https://coa.local/entity/customer-42"
 *     ]
 *   ],
 *   truncated: false,
 *   variables: [
 *     "s"
 *   ]
 * }
 * *\/
 * ```
 *
 * @example Ask whether any triple exists
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   sparql: "ASK { ?s ?p ?o }"
 * };
 * const command = new RunSparqlCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   answer: true,
 *   elapsedMs: 12,
 *   form: "ASK",
 *   graphCount: 2,
 *   returnedRows: 0,
 *   rowCount: 0,
 *   truncated: false
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RunSparqlCommand extends $Command
  .classBuilder<
    RunSparqlCommandInput,
    RunSparqlCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "RunSparql", {})
  .n("DataLayerServiceClient", "RunSparqlCommand")
  .sc(RunSparql$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RunSparqlInput;
      output: RunSparqlOutput;
    };
    sdk: {
      input: RunSparqlCommandInput;
      output: RunSparqlCommandOutput;
    };
  };
}
