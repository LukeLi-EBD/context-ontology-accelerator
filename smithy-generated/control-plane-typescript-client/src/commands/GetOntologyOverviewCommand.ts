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
import type { GetOntologyOverviewInput, OntologyOverview } from "../models/models_0";
import { GetOntologyOverview$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologyOverviewCommand}.
 */
export interface GetOntologyOverviewCommandInput extends GetOntologyOverviewInput {}
/**
 * @public
 *
 * The output of {@link GetOntologyOverviewCommand}.
 */
export interface GetOntologyOverviewCommandOutput extends OntologyOverview, __MetadataBearer {}

/**
 * Enumerate the classes + properties persisted in one ontology's graph.
 *
 * Reads the ontology's named graph directly, returning its classes,
 * object properties (relationships), and datatype properties. Used by the
 * web UI's induced-ontology detail view.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologyOverviewCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologyOverviewCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologyOverviewInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   limit: Number("int"),
 *   offset: Number("int"),
 *   sample: true || false,
 * };
 * const command = new GetOntologyOverviewCommand(input);
 * const response = await client.send(command);
 * // { // OntologyOverview
 * //   ontologyId: "STRING_VALUE", // required
 * //   namespace: "STRING_VALUE", // required
 * //   graphUri: "STRING_VALUE",
 * //   classes: [ // OntologyClassSummaryList
 * //     { // OntologyClassSummary
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       comment: "STRING_VALUE",
 * //       groundedTo: "STRING_VALUE",
 * //       matchType: "STRING_VALUE",
 * //       subClassOf: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * //   objectProperties: [ // OntologyPropertySummaryList
 * //     { // OntologyPropertySummary
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       domain: "STRING_VALUE",
 * //       range: "STRING_VALUE",
 * //     },
 * //   ],
 * //   datatypeProperties: [
 * //     {
 * //       uri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE",
 * //       domain: "STRING_VALUE",
 * //       range: "STRING_VALUE",
 * //     },
 * //   ],
 * //   totalClasses: Number("int"),
 * //   totalObjectProperties: Number("int"),
 * //   totalDatatypeProperties: Number("int"),
 * // };
 *
 * ```
 *
 * @param GetOntologyOverviewCommandInput - {@link GetOntologyOverviewCommandInput}
 * @returns {@link GetOntologyOverviewCommandOutput}
 * @see {@link GetOntologyOverviewCommandInput} for command's `input` shape.
 * @see {@link GetOntologyOverviewCommandOutput} for command's `response` shape.
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
 * @example Enumerate the classes and properties in an ontology's graph
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "http://coa.amazon.com/onto/sales-crm"
 * };
 * const command = new GetOntologyOverviewCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   classes: [
 *     {
 *       comment: "A party that purchases goods or services.",
 *       groundedTo: "urn:coa:class:Party",
 *       label: "Customer",
 *       matchType: "close",
 *       uri: "http://example.com/onto#Customer"
 *     }
 *   ],
 *   datatypeProperties: [
 *     {
 *       domain: "http://example.com/onto#Customer",
 *       label: "email address",
 *       range: "http://www.w3.org/2001/XMLSchema#string",
 *       uri: "http://example.com/onto#emailAddress"
 *     }
 *   ],
 *   graphUri: "http://coa.amazon.com/onto/sales-crm",
 *   namespace: "sales-analytics",
 *   objectProperties: [
 *     {
 *       domain: "http://example.com/onto#Customer",
 *       label: "placed order",
 *       range: "http://example.com/onto#Order",
 *       uri: "http://example.com/onto#placedOrder"
 *     }
 *   ],
 *   ontologyId: "http://coa.amazon.com/onto/sales-crm",
 *   totalClasses: 1,
 *   totalDatatypeProperties: 1,
 *   totalObjectProperties: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologyOverviewCommand extends $Command
  .classBuilder<
    GetOntologyOverviewCommandInput,
    GetOntologyOverviewCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntologyOverview", {})
  .n("ControlPlaneServiceClient", "GetOntologyOverviewCommand")
  .sc(GetOntologyOverview$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologyOverviewInput;
      output: OntologyOverview;
    };
    sdk: {
      input: GetOntologyOverviewCommandInput;
      output: GetOntologyOverviewCommandOutput;
    };
  };
}
