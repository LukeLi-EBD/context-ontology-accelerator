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
import type { ListOntologyVersionsInput, OntologyVersionPage } from "../models/models_1";
import { ListOntologyVersions$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListOntologyVersionsCommand}.
 */
export interface ListOntologyVersionsCommandInput extends ListOntologyVersionsInput {}
/**
 * @public
 *
 * The output of {@link ListOntologyVersionsCommand}.
 */
export interface ListOntologyVersionsCommandOutput extends OntologyVersionPage, __MetadataBearer {}

/**
 * List the versions of one ontology.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListOntologyVersionsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListOntologyVersionsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListOntologyVersionsInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 * };
 * const command = new ListOntologyVersionsCommand(input);
 * const response = await client.send(command);
 * // { // OntologyVersionPage
 * //   items: [ // OntologyVersionList // required
 * //     { // OntologyVersion
 * //       id: "STRING_VALUE", // required
 * //       semver: "STRING_VALUE", // required
 * //       status: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated", // required
 * //       contentHash: "STRING_VALUE",
 * //       tripleCount: Number("int"),
 * //       format: "STRING_VALUE",
 * //       graph: "STRING_VALUE",
 * //       rollbackOf: "STRING_VALUE",
 * //       label: "STRING_VALUE",
 * //       createdAt: "STRING_VALUE",
 * //       publishedAt: "STRING_VALUE",
 * //     },
 * //   ],
 * //   count: Number("int"), // required
 * //   total: Number("int"), // required
 * //   deprecated: Number("int"), // required
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
 * @param ListOntologyVersionsCommandInput - {@link ListOntologyVersionsCommandInput}
 * @returns {@link ListOntologyVersionsCommandOutput}
 * @see {@link ListOntologyVersionsCommandInput} for command's `input` shape.
 * @see {@link ListOntologyVersionsCommandOutput} for command's `response` shape.
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
 * @example List versions with the current pointer
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core"
 * };
 * const command = new ListOntologyVersionsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   count: 1,
 *   deprecated: 0,
 *   items: [
 *     {
 *       createdAt: "2026-10-01T08:00:00Z",
 *       graph: "urn:platform:graph:tbox:1a2b3c4d",
 *       id: "ont-1a2b3c4d5e6f",
 *       publishedAt: "2026-10-02T09:30:00Z",
 *       semver: "1.0.0",
 *       status: "published",
 *       tripleCount: 1280
 *     }
 *   ],
 *   pointer: {
 *     graph: "urn:platform:graph:tbox:1a2b3c4d",
 *     name: "tbox/current",
 *     semver: "1.0.0",
 *     updatedAt: "2026-10-02T09:30:00Z",
 *     versionId: "ont-1a2b3c4d5e6f"
 *   },
 *   total: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListOntologyVersionsCommand extends $Command
  .classBuilder<
    ListOntologyVersionsCommandInput,
    ListOntologyVersionsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListOntologyVersions", {})
  .n("ControlPlaneServiceClient", "ListOntologyVersionsCommand")
  .sc(ListOntologyVersions$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListOntologyVersionsInput;
      output: OntologyVersionPage;
    };
    sdk: {
      input: ListOntologyVersionsCommandInput;
      output: ListOntologyVersionsCommandOutput;
    };
  };
}
