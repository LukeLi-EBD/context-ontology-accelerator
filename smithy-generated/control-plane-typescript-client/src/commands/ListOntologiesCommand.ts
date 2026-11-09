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
import type { ListOntologiesInput, ListOntologiesOutput } from "../models/models_0";
import { ListOntologies$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListOntologiesCommand}.
 */
export interface ListOntologiesCommandInput extends ListOntologiesInput {}
/**
 * @public
 *
 * The output of {@link ListOntologiesCommand}.
 */
export interface ListOntologiesCommandOutput extends ListOntologiesOutput, __MetadataBearer {}

/**
 * List ontologies registered in a namespace, one page at a time.
 *
 * A page can hold fewer than `maxResults` ontologies, or none, while
 * `nextToken` is present: each request reads a bounded slice of the registry.
 * Keep paging until `nextToken` is absent.
 *
 * The server also binds a legacy `skip` query parameter (an offset applied
 * before the page, up to 10000). It predates `nextToken`, is kept for existing
 * callers, and is deliberately not modelled: use `nextToken`.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListOntologiesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListOntologiesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListOntologiesInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyType: "foundational" || "induced" || "user_created" || "user_uploaded",
 *   domainTag: "STRING_VALUE",
 *   uri: "STRING_VALUE",
 *   sourceRegistry: "STRING_VALUE",
 *   licenseTier: "STRING_VALUE",
 *   limit: Number("int"),
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListOntologiesCommand(input);
 * const response = await client.send(command);
 * // { // ListOntologiesOutput
 * //   nextToken: "STRING_VALUE",
 * //   ontologies: [ // OntologyRecordList // required
 * //     { // OntologyRecord
 * //       ontologyId: "STRING_VALUE", // required
 * //       uri: "STRING_VALUE", // required
 * //       title: "STRING_VALUE",
 * //       description: "STRING_VALUE",
 * //       ontologyType: "STRING_VALUE",
 * //       parseStatus: "STRING_VALUE",
 * //       status: "STRING_VALUE",
 * //       deleteError: "STRING_VALUE",
 * //       format: "STRING_VALUE",
 * //       domainTags: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
 * //       classCount: Number("int"),
 * //       propertyCount: Number("int"),
 * //       axiomCount: Number("int"),
 * //       embeddingCount: Number("int"),
 * //       graphUri: "STRING_VALUE",
 * //       createdAt: "STRING_VALUE",
 * //       updatedAt: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListOntologiesCommandInput - {@link ListOntologiesCommandInput}
 * @returns {@link ListOntologiesCommandOutput}
 * @see {@link ListOntologiesCommandInput} for command's `input` shape.
 * @see {@link ListOntologiesCommandOutput} for command's `response` shape.
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
 * @example List induced ontologies in a namespace
 * ```javascript
 * //
 * const input = {
 *   maxResults: 20,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyType: "induced"
 * };
 * const command = new ListOntologiesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   ontologies: [
 *     {
 *       axiomCount: 210,
 *       classCount: 12,
 *       createdAt: "2026-07-20T14:03:11Z",
 *       description: "Induced ontology for the CRM sales schema.",
 *       domainTags: [
 *         "sales",
 *         "crm"
 *       ],
 *       embeddingCount: 46,
 *       format: "text/turtle",
 *       graphUri: "http://coa.amazon.com/onto/sales-crm",
 *       ontologyId: "http://coa.amazon.com/onto/sales-crm",
 *       ontologyType: "induced",
 *       propertyCount: 34,
 *       title: "Sales CRM",
 *       updatedAt: "2026-07-21T09:15:42Z",
 *       uri: "http://coa.amazon.com/onto/sales-crm"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListOntologiesCommand extends $Command
  .classBuilder<
    ListOntologiesCommandInput,
    ListOntologiesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListOntologies", {})
  .n("ControlPlaneServiceClient", "ListOntologiesCommand")
  .sc(ListOntologies$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListOntologiesInput;
      output: ListOntologiesOutput;
    };
    sdk: {
      input: ListOntologiesCommandInput;
      output: ListOntologiesCommandOutput;
    };
  };
}
