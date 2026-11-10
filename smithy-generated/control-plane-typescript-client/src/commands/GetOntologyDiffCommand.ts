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
import type { GetOntologyDiffInput, GetOntologyDiffOutput } from "../models/models_0";
import { GetOntologyDiff$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologyDiffCommand}.
 */
export interface GetOntologyDiffCommandInput extends GetOntologyDiffInput {}
/**
 * @public
 *
 * The output of {@link GetOntologyDiffCommand}.
 */
export interface GetOntologyDiffCommandOutput extends GetOntologyDiffOutput, __MetadataBearer {}

/**
 * Compare two named graphs in the same namespace, read-only.
 *
 * ``from`` is the baseline and ``to`` the target; added means present in
 * ``to`` and absent from ``from``. Both IRIs must belong to this namespace,
 * so an arbitrary graph cannot be read through the diff.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologyDiffCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologyDiffCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologyDiffInput
 *   namespaceId: "STRING_VALUE", // required
 *   fromGraph: "STRING_VALUE", // required
 *   toGraph: "STRING_VALUE", // required
 *   limit: Number("int"),
 * };
 * const command = new GetOntologyDiffCommand(input);
 * const response = await client.send(command);
 * // { // GetOntologyDiffOutput
 * //   baselineGraph: "STRING_VALUE", // required
 * //   targetGraph: "STRING_VALUE", // required
 * //   counts: { // OntologyDiffCounts
 * //     addedTriples: Number("int"), // required
 * //     removedTriples: Number("int"), // required
 * //     addedClasses: Number("int"), // required
 * //     removedClasses: Number("int"), // required
 * //     addedProperties: Number("int"), // required
 * //     removedProperties: Number("int"), // required
 * //   },
 * //   addedClasses: [ // OntologyDiffStringList // required
 * //     "STRING_VALUE",
 * //   ],
 * //   removedClasses: [ // required
 * //     "STRING_VALUE",
 * //   ],
 * //   addedProperties: [ // required
 * //     "STRING_VALUE",
 * //   ],
 * //   removedProperties: [ // required
 * //     "STRING_VALUE",
 * //   ],
 * //   examples: { // OntologyDiffExamples
 * //     addedTriples: [ // TripleExampleList // required
 * //       { // TripleExample
 * //         subject: "STRING_VALUE", // required
 * //         predicate: "STRING_VALUE", // required
 * //         object: "STRING_VALUE", // required
 * //       },
 * //     ],
 * //     removedTriples: [ // required
 * //       {
 * //         subject: "STRING_VALUE", // required
 * //         predicate: "STRING_VALUE", // required
 * //         object: "STRING_VALUE", // required
 * //       },
 * //     ],
 * //   },
 * //   truncated: true || false, // required
 * //   source: "STRING_VALUE", // required
 * //   sampledAt: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param GetOntologyDiffCommandInput - {@link GetOntologyDiffCommandInput}
 * @returns {@link GetOntologyDiffCommandOutput}
 * @see {@link GetOntologyDiffCommandInput} for command's `input` shape.
 * @see {@link GetOntologyDiffCommandOutput} for command's `response` shape.
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
 * @example Diff a baseline graph against a newer one
 * ```javascript
 * //
 * const input = {
 *   fromGraph: "http://coa.amazon.com/onto/sales-crm-v1",
 *   limit: 20,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   toGraph: "http://coa.amazon.com/onto/sales-crm-v2"
 * };
 * const command = new GetOntologyDiffCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   addedClasses: [
 *     "http://example.com/onto#LoyaltyAccount"
 *   ],
 *   addedProperties: [
 *     "http://example.com/onto#loyaltyTier"
 *   ],
 *   baselineGraph: "http://coa.amazon.com/onto/sales-crm-v1",
 *   counts: {
 *     addedClasses: 1,
 *     addedProperties: 2,
 *     addedTriples: 12,
 *     removedClasses: 0,
 *     removedProperties: 1,
 *     removedTriples: 3
 *   },
 *   examples: {
 *     addedTriples: [
 *       {
 *         object: "http://www.w3.org/2002/07/owl#Class",
 *         predicate: "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
 *         subject: "http://example.com/onto#LoyaltyAccount"
 *       }
 *     ],
 *     removedTriples:     []
 *   },
 *   removedClasses:   [],
 *   removedProperties: [
 *     "http://example.com/onto#legacyCode"
 *   ],
 *   sampledAt: "2026-11-10T09:00:00Z",
 *   source: "SPARQL MINUS over the two named graphs",
 *   targetGraph: "http://coa.amazon.com/onto/sales-crm-v2",
 *   truncated: false
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologyDiffCommand extends $Command
  .classBuilder<
    GetOntologyDiffCommandInput,
    GetOntologyDiffCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntologyDiff", {})
  .n("ControlPlaneServiceClient", "GetOntologyDiffCommand")
  .sc(GetOntologyDiff$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologyDiffInput;
      output: GetOntologyDiffOutput;
    };
    sdk: {
      input: GetOntologyDiffCommandInput;
      output: GetOntologyDiffCommandOutput;
    };
  };
}
