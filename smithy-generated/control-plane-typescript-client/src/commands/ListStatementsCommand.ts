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
import type { ListStatementsInput, ListStatementsOutput } from "../models/models_0";
import { ListStatements$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListStatementsCommand}.
 */
export interface ListStatementsCommandInput extends ListStatementsInput {}
/**
 * @public
 *
 * The output of {@link ListStatementsCommand}.
 */
export interface ListStatementsCommandOutput extends ListStatementsOutput, __MetadataBearer {}

/**
 * Enumerate the statements in a namespace's named graphs.
 *
 * Read-only and namespace-scoped: the query only ever sees graphs under the
 * namespace's prefix, and each filter narrows that set (they combine with
 * AND). Subject / predicate are IRIs; object is an IRI when it starts with
 * ``http://``, ``https://`` or ``urn:`` and a literal lexical form otherwise.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListStatementsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListStatementsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListStatementsInput
 *   namespaceId: "STRING_VALUE", // required
 *   subject: "STRING_VALUE",
 *   predicate: "STRING_VALUE",
 *   objectValue: "STRING_VALUE",
 *   graph: "STRING_VALUE",
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new ListStatementsCommand(input);
 * const response = await client.send(command);
 * // { // ListStatementsOutput
 * //   statements: [ // GraphStatementList // required
 * //     { // GraphStatement
 * //       graph: "STRING_VALUE", // required
 * //       subject: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       object: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   truncated: true || false,
 * // };
 *
 * ```
 *
 * @param ListStatementsCommandInput - {@link ListStatementsCommandInput}
 * @returns {@link ListStatementsCommandOutput}
 * @see {@link ListStatementsCommandInput} for command's `input` shape.
 * @see {@link ListStatementsCommandOutput} for command's `response` shape.
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
 * @example List the statements that mention one subject
 * ```javascript
 * //
 * const input = {
 *   limit: 2,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   subject: "http://example.com/onto#Customer"
 * };
 * const command = new ListStatementsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   statements: [
 *     {
 *       graph: "http://coa.amazon.com/onto/sales-crm",
 *       object: "Customer",
 *       predicate: "http://www.w3.org/2000/01/rdf-schema#label",
 *       subject: "http://example.com/onto#Customer"
 *     },
 *     {
 *       graph: "http://coa.amazon.com/onto/sales-crm",
 *       object: "http://www.w3.org/2002/07/owl#Class",
 *       predicate: "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
 *       subject: "http://example.com/onto#Customer"
 *     }
 *   ],
 *   truncated: false
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListStatementsCommand extends $Command
  .classBuilder<
    ListStatementsCommandInput,
    ListStatementsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListStatements", {})
  .n("ControlPlaneServiceClient", "ListStatementsCommand")
  .sc(ListStatements$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListStatementsInput;
      output: ListStatementsOutput;
    };
    sdk: {
      input: ListStatementsCommandInput;
      output: ListStatementsCommandOutput;
    };
  };
}
