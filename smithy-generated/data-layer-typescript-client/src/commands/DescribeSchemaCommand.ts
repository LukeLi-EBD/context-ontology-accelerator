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
import type { DescribeSchemaInput, DescribeSchemaOutput } from "../models/models_0";
import { DescribeSchema$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DescribeSchemaCommand}.
 */
export interface DescribeSchemaCommandInput extends DescribeSchemaInput {}
/**
 * @public
 *
 * The output of {@link DescribeSchemaCommand}.
 */
export interface DescribeSchemaCommandOutput extends DescribeSchemaOutput, __MetadataBearer {}

/**
 * Describe the namespace's queryable schema: classes and their properties
 * across every ontology loaded into the namespace (induced, foundational,
 * uploaded). Proxies to the ontology-engine ``/graph/schema`` route via the
 * ontology-api-proxy Lambda — the same source the MCP ``describe_schema``
 * tool reads, so an agent and a UI see the same schema.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, DescribeSchemaCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, DescribeSchemaCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // DescribeSchemaInput
 *   namespaceId: "STRING_VALUE", // required
 *   includeProperties: true || false,
 *   maxResults: Number("int"),
 * };
 * const command = new DescribeSchemaCommand(input);
 * const response = await client.send(command);
 * // { // DescribeSchemaOutput
 * //   classes: [ // SchemaClassList // required
 * //     { // SchemaClass
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       description: "STRING_VALUE",
 * //       properties: [ // SchemaPropertyList
 * //         { // SchemaProperty
 * //           uri: "STRING_VALUE", // required
 * //           label: "STRING_VALUE", // required
 * //           range: "STRING_VALUE",
 * //           description: "STRING_VALUE",
 * //         },
 * //       ],
 * //       parentClass: "STRING_VALUE",
 * //     },
 * //   ],
 * //   ontologyVersion: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param DescribeSchemaCommandInput - {@link DescribeSchemaCommandInput}
 * @returns {@link DescribeSchemaCommandOutput}
 * @see {@link DescribeSchemaCommandInput} for command's `input` shape.
 * @see {@link DescribeSchemaCommandOutput} for command's `response` shape.
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
 * @example Describe the queryable schema
 * ```javascript
 * //
 * const input = {
 *   includeProperties: true,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new DescribeSchemaCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   classes: [
 *     {
 *       description: "A purchasing organization or individual",
 *       label: "Customer",
 *       properties: [
 *         {
 *           label: "segment",
 *           range: "xsd:string",
 *           uri: "urn:coa:prop:segment"
 *         }
 *       ],
 *       uri: "urn:coa:class:Customer"
 *     }
 *   ],
 *   ontologyVersion: "2025-09-01"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class DescribeSchemaCommand extends $Command
  .classBuilder<
    DescribeSchemaCommandInput,
    DescribeSchemaCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "DescribeSchema", {})
  .n("DataLayerServiceClient", "DescribeSchemaCommand")
  .sc(DescribeSchema$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DescribeSchemaInput;
      output: DescribeSchemaOutput;
    };
    sdk: {
      input: DescribeSchemaCommandInput;
      output: DescribeSchemaCommandOutput;
    };
  };
}
