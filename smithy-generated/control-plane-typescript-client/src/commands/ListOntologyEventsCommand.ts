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
import type { ListOntologyEventsInput, OntologyEventPage } from "../models/models_1";
import { ListOntologyEvents$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListOntologyEventsCommand}.
 */
export interface ListOntologyEventsCommandInput extends ListOntologyEventsInput {}
/**
 * @public
 *
 * The output of {@link ListOntologyEventsCommand}.
 */
export interface ListOntologyEventsCommandOutput extends OntologyEventPage, __MetadataBearer {}

/**
 * List the hash-chained lifecycle audit events for one ontology.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListOntologyEventsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListOntologyEventsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListOntologyEventsInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   versionId: "STRING_VALUE",
 *   action: "STRING_VALUE",
 *   limit: Number("int"),
 * };
 * const command = new ListOntologyEventsCommand(input);
 * const response = await client.send(command);
 * // { // OntologyEventPage
 * //   items: [ // OntologyEventList // required
 * //     { // OntologyEvent
 * //       eventId: Number("long"), // required
 * //       versionId: "STRING_VALUE",
 * //       proposalId: "STRING_VALUE",
 * //       action: "STRING_VALUE", // required
 * //       actor: "STRING_VALUE", // required
 * //       reason: "STRING_VALUE",
 * //       payload: "DOCUMENT_VALUE",
 * //       prevEvent: Number("long"),
 * //       hash: "STRING_VALUE",
 * //       createdAt: "STRING_VALUE", // required
 * //       type: "STRING_VALUE",
 * //       at: "STRING_VALUE",
 * //       category: "STRING_VALUE",
 * //     },
 * //   ],
 * //   count: Number("int"), // required
 * //   categories: { // OntologyCategoryCounts
 * //     "<keys>": Number("int"),
 * //   },
 * //   filter: { // OntologyEventFilter
 * //     versionId: "STRING_VALUE",
 * //     action: "STRING_VALUE",
 * //   },
 * //   current: { // OntologyPointer
 * //     name: "STRING_VALUE",
 * //     versionId: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE",
 * //     contentHash: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     updatedAt: "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param ListOntologyEventsCommandInput - {@link ListOntologyEventsCommandInput}
 * @returns {@link ListOntologyEventsCommandOutput}
 * @see {@link ListOntologyEventsCommandInput} for command's `input` shape.
 * @see {@link ListOntologyEventsCommandOutput} for command's `response` shape.
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
 * @example List publish and rollback events
 * ```javascript
 * //
 * const input = {
 *   limit: 50,
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core"
 * };
 * const command = new ListOntologyEventsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   categories: {
 *     other: 0,
 *     published: 1,
 *     rolled_back: 0,
 *     superseded: 0
 *   },
 *   count: 1,
 *   items: [
 *     {
 *       action: "published",
 *       actor: "operator",
 *       at: "2026-10-02T09:30:00Z",
 *       category: "published",
 *       createdAt: "2026-10-02T09:30:00Z",
 *       eventId: 41,
 *       type: "published",
 *       versionId: "ont-1a2b3c4d5e6f"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListOntologyEventsCommand extends $Command
  .classBuilder<
    ListOntologyEventsCommandInput,
    ListOntologyEventsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListOntologyEvents", {})
  .n("ControlPlaneServiceClient", "ListOntologyEventsCommand")
  .sc(ListOntologyEvents$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListOntologyEventsInput;
      output: OntologyEventPage;
    };
    sdk: {
      input: ListOntologyEventsCommandInput;
      output: ListOntologyEventsCommandOutput;
    };
  };
}
