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
import type { DiffOntologyVersionsInput, OntologyDiff } from "../models/models_1";
import { DiffOntologyVersions$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DiffOntologyVersionsCommand}.
 */
export interface DiffOntologyVersionsCommandInput extends DiffOntologyVersionsInput {}
/**
 * @public
 *
 * The output of {@link DiffOntologyVersionsCommand}.
 */
export interface DiffOntologyVersionsCommandOutput extends OntologyDiff, __MetadataBearer {}

/**
 * Diff one version against another (or against the publish baseline).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, DiffOntologyVersionsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, DiffOntologyVersionsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // DiffOntologyVersionsInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   versionId: "STRING_VALUE", // required
 *   against: "STRING_VALUE",
 * };
 * const command = new DiffOntologyVersionsCommand(input);
 * const response = await client.send(command);
 * // { // OntologyDiff
 * //   from: "STRING_VALUE",
 * //   to: "STRING_VALUE", // required
 * //   breaking: true || false, // required
 * //   breakingItems: [ // OntologyBreakingItemList // required
 * //     { // OntologyBreakingItem
 * //       kind: "STRING_VALUE", // required
 * //       iri: "STRING_VALUE",
 * //       property: "STRING_VALUE",
 * //       from: [ // OntologyStringList
 * //         "STRING_VALUE",
 * //       ],
 * //       to: [
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * //   summary: { // OntologyDiffSummary
 * //     addedTriples: Number("int"), // required
 * //     removedTriples: Number("int"), // required
 * //     addedClasses: [ // required
 * //       "STRING_VALUE",
 * //     ],
 * //     removedClasses: [ // required
 * //       "STRING_VALUE",
 * //     ],
 * //     addedProperties: [ // required
 * //       "STRING_VALUE",
 * //     ],
 * //     removedProperties: "<OntologyStringList>", // required
 * //     domainChanges: [ // OntologyDomainChangeList // required
 * //       { // OntologyDomainChange
 * //         property: "STRING_VALUE", // required
 * //         from: "<OntologyStringList>", // required
 * //         to: "<OntologyStringList>", // required
 * //       },
 * //     ],
 * //     rangeChanges: [ // required
 * //       {
 * //         property: "STRING_VALUE", // required
 * //         from: "<OntologyStringList>", // required
 * //         to: "<OntologyStringList>", // required
 * //       },
 * //     ],
 * //     removedClassInstances: [ // OntologyClassInstanceList // required
 * //       { // OntologyClassInstance
 * //         class: "STRING_VALUE", // required
 * //         instances: Number("int"), // required
 * //       },
 * //     ],
 * //   },
 * //   markdown: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param DiffOntologyVersionsCommandInput - {@link DiffOntologyVersionsCommandInput}
 * @returns {@link DiffOntologyVersionsCommandOutput}
 * @see {@link DiffOntologyVersionsCommandInput} for command's `input` shape.
 * @see {@link DiffOntologyVersionsCommandOutput} for command's `response` shape.
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
 * @example Diff a draft against the current version
 * ```javascript
 * //
 * const input = {
 *   against: "ont-1a2b3c4d5e6f",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   versionId: "ont-draft-9f8e7d6c5b4a"
 * };
 * const command = new DiffOntologyVersionsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   breaking: false,
 *   breakingItems:   [],
 *   from: "ont-1a2b3c4d5e6f",
 *   summary: {
 *     addedClasses: [
 *       "https://example.com/ontology/core#Invoice"
 *     ],
 *     addedProperties:     [],
 *     addedTriples: 12,
 *     domainChanges:     [],
 *     rangeChanges:     [],
 *     removedClassInstances:     [],
 *     removedClasses:     [],
 *     removedProperties:     [],
 *     removedTriples: 0
 *   },
 *   to: "ont-draft-9f8e7d6c5b4a"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class DiffOntologyVersionsCommand extends $Command
  .classBuilder<
    DiffOntologyVersionsCommandInput,
    DiffOntologyVersionsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "DiffOntologyVersions", {})
  .n("ControlPlaneServiceClient", "DiffOntologyVersionsCommand")
  .sc(DiffOntologyVersions$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DiffOntologyVersionsInput;
      output: OntologyDiff;
    };
    sdk: {
      input: DiffOntologyVersionsCommandInput;
      output: DiffOntologyVersionsCommandOutput;
    };
  };
}
