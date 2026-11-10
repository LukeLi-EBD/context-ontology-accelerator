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
import type { ListOntologyInstancesInput, OntologyInstanceList } from "../models/models_0";
import { ListOntologyInstances$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListOntologyInstancesCommand}.
 */
export interface ListOntologyInstancesCommandInput extends ListOntologyInstancesInput {}
/**
 * @public
 *
 * The output of {@link ListOntologyInstancesCommand}.
 */
export interface ListOntologyInstancesCommandOutput extends OntologyInstanceList, __MetadataBearer {}

/**
 * List instances of one ontology class.
 *
 * `limit` caps the returned page; `total` still reports the full instance
 * count so the caller can show "N of M".
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListOntologyInstancesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListOntologyInstancesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListOntologyInstancesInput
 *   classIri: "STRING_VALUE", // required
 *   limit: Number("int"),
 *   offset: Number("int"),
 * };
 * const command = new ListOntologyInstancesCommand(input);
 * const response = await client.send(command);
 * // { // OntologyInstanceList
 * //   class: "STRING_VALUE", // required
 * //   items: [ // OntologyInstanceRefList // required
 * //     { // OntologyInstanceRef
 * //       iri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       graph: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   total: Number("int"), // required
 * //   limit: Number("int"), // required
 * //   offset: Number("int"), // required
 * //   pointer: { // OntologyPointer
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
 * @param ListOntologyInstancesCommandInput - {@link ListOntologyInstancesCommandInput}
 * @returns {@link ListOntologyInstancesCommandOutput}
 * @see {@link ListOntologyInstancesCommandInput} for command's `input` shape.
 * @see {@link ListOntologyInstancesCommandOutput} for command's `response` shape.
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
 * @example List instances of a class
 * ```javascript
 * //
 * const input = {
 *   classIri: "urn:coa:class:BusinessEntity",
 *   limit: 5
 * };
 * const command = new ListOntologyInstancesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   class: "urn:coa:class:BusinessEntity",
 *   items: [
 *     {
 *       graph: "urn:platform:graph:abox",
 *       iri: "urn:coa:entity:contract-ledger",
 *       label: "Contract Ledger"
 *     }
 *   ],
 *   limit: 5,
 *   offset: 0,
 *   total: 12
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListOntologyInstancesCommand extends $Command
  .classBuilder<
    ListOntologyInstancesCommandInput,
    ListOntologyInstancesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListOntologyInstances", {})
  .n("ControlPlaneServiceClient", "ListOntologyInstancesCommand")
  .sc(ListOntologyInstances$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListOntologyInstancesInput;
      output: OntologyInstanceList;
    };
    sdk: {
      input: ListOntologyInstancesCommandInput;
      output: ListOntologyInstancesCommandOutput;
    };
  };
}
