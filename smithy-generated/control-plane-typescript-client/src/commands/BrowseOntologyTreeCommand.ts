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
import type { OntologyTreeResult } from "../models/models_1";
import { BrowseOntologyTree$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link BrowseOntologyTreeCommand}.
 */
export interface BrowseOntologyTreeCommandInput {}
/**
 * @public
 *
 * The output of {@link BrowseOntologyTreeCommand}.
 */
export interface BrowseOntologyTreeCommandOutput extends OntologyTreeResult, __MetadataBearer {}

/**
 * Read the class hierarchy, flat class list and property list.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, BrowseOntologyTreeCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, BrowseOntologyTreeCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = {};
 * const command = new BrowseOntologyTreeCommand(input);
 * const response = await client.send(command);
 * // { // OntologyTreeResult
 * //   pointer: { // OntologyPointer
 * //     name: "STRING_VALUE",
 * //     versionId: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE",
 * //     contentHash: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     updatedAt: "STRING_VALUE",
 * //   },
 * //   tree: [ // OntologyTreeNodeList // required
 * //     { // OntologyTreeNode
 * //       iri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       parents: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
 * //       children: [
 * //         {
 * //           iri: "STRING_VALUE", // required
 * //           label: "STRING_VALUE", // required
 * //           parents: [
 * //             "STRING_VALUE",
 * //           ],
 * //           children: "<OntologyTreeNodeList>",
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   classes: [ // OntologyClassRefList // required
 * //     { // OntologyClassRef
 * //       iri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       parents: [
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * //   properties: [ // OntologyPropertyRefList // required
 * //     { // OntologyPropertyRef
 * //       iri: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       kind: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   counts: { // OntologyBrowseCounts
 * //     classes: Number("int"), // required
 * //     properties: Number("int"), // required
 * //   },
 * // };
 *
 * ```
 *
 * @param BrowseOntologyTreeCommandInput - {@link BrowseOntologyTreeCommandInput}
 * @returns {@link BrowseOntologyTreeCommandOutput}
 * @see {@link BrowseOntologyTreeCommandInput} for command's `input` shape.
 * @see {@link BrowseOntologyTreeCommandOutput} for command's `response` shape.
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
 * @example Read the published class tree
 * ```javascript
 * //
 * const input = { /* empty *\/ };
 * const command = new BrowseOntologyTreeCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   classes: [
 *     {
 *       iri: "urn:coa:class:BusinessEntity",
 *       label: "Business Entity",
 *       parents:       []
 *     },
 *     {
 *       iri: "urn:coa:class:Contract",
 *       label: "Contract",
 *       parents: [
 *         "urn:coa:class:BusinessEntity"
 *       ]
 *     }
 *   ],
 *   counts: {
 *     classes: 2,
 *     properties: 1
 *   },
 *   pointer: {
 *     graph: "urn:platform:graph:tbox:1a2b3c4d",
 *     name: "tbox/current",
 *     semver: "1.0.0",
 *     updatedAt: "2026-10-02T09:30:00Z",
 *     versionId: "ont-1a2b3c4d5e6f"
 *   },
 *   properties: [
 *     {
 *       iri: "urn:coa:property:belongs-to",
 *       kind: "ObjectProperty",
 *       label: "belongs to"
 *     }
 *   ],
 *   tree: [
 *     {
 *       children: [
 *         {
 *           children:           [],
 *           iri: "urn:coa:class:Contract",
 *           label: "Contract",
 *           parents: [
 *             "urn:coa:class:BusinessEntity"
 *           ]
 *         }
 *       ],
 *       iri: "urn:coa:class:BusinessEntity",
 *       label: "Business Entity",
 *       parents:       []
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class BrowseOntologyTreeCommand extends $Command
  .classBuilder<
    BrowseOntologyTreeCommandInput,
    BrowseOntologyTreeCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "BrowseOntologyTree", {})
  .n("ControlPlaneServiceClient", "BrowseOntologyTreeCommand")
  .sc(BrowseOntologyTree$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: {};
      output: OntologyTreeResult;
    };
    sdk: {
      input: BrowseOntologyTreeCommandInput;
      output: BrowseOntologyTreeCommandOutput;
    };
  };
}
