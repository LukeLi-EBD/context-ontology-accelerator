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
import type { OntologyRollbackResult, RollbackOntologyInput } from "../models/models_1";
import { RollbackOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RollbackOntologyCommand}.
 */
export interface RollbackOntologyCommandInput extends RollbackOntologyInput {}
/**
 * @public
 *
 * The output of {@link RollbackOntologyCommand}.
 */
export interface RollbackOntologyCommandOutput extends OntologyRollbackResult, __MetadataBearer {}

/**
 * Roll the `tbox/current` pointer back to an earlier version.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RollbackOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RollbackOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RollbackOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   targetVersionId: "STRING_VALUE", // required
 *   mode: "POINTER_ONLY" || "NEW_VERSION", // required
 *   expectedVersionId: "STRING_VALUE",
 *   planOnly: true || false,
 *   actor: "STRING_VALUE",
 *   reason: "STRING_VALUE",
 * };
 * const command = new RollbackOntologyCommand(input);
 * const response = await client.send(command);
 * // { // OntologyRollbackResult
 * //   ok: true || false,
 * //   mode: "POINTER_ONLY" || "NEW_VERSION",
 * //   target: { // OntologyVersion
 * //     id: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE", // required
 * //     status: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated", // required
 * //     contentHash: "STRING_VALUE",
 * //     tripleCount: Number("int"),
 * //     format: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     rollbackOf: "STRING_VALUE",
 * //     label: "STRING_VALUE",
 * //     createdAt: "STRING_VALUE",
 * //     publishedAt: "STRING_VALUE",
 * //   },
 * //   replacedVersion: {
 * //     id: "STRING_VALUE", // required
 * //     semver: "STRING_VALUE", // required
 * //     status: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated", // required
 * //     contentHash: "STRING_VALUE",
 * //     tripleCount: Number("int"),
 * //     format: "STRING_VALUE",
 * //     graph: "STRING_VALUE",
 * //     rollbackOf: "STRING_VALUE",
 * //     label: "STRING_VALUE",
 * //     createdAt: "STRING_VALUE",
 * //     publishedAt: "STRING_VALUE",
 * //   },
 * //   targetVersionId: "STRING_VALUE",
 * //   targetTriples: Number("int"),
 * //   replacedVersionId: "STRING_VALUE",
 * //   id: "STRING_VALUE",
 * //   publishedVersion: "STRING_VALUE",
 * //   rollbackOf: "STRING_VALUE",
 * //   semver: "STRING_VALUE",
 * //   status: "draft" || "proposed" || "review" || "approved" || "published" || "superseded" || "rejected" || "deprecated",
 * //   graph: "STRING_VALUE",
 * //   contentHash: "STRING_VALUE",
 * //   triples: Number("int"),
 * //   previous: "STRING_VALUE",
 * //   wouldChangePointer: true || false,
 * //   unchanged: true || false,
 * //   publishedBy: "STRING_VALUE",
 * //   publishedAt: "STRING_VALUE",
 * //   rolledBackAt: "STRING_VALUE",
 * //   rolledBackBy: "STRING_VALUE",
 * //   reason: "STRING_VALUE",
 * //   blockers: [ // OntologyBlockerList
 * //     { // PublishBlocker
 * //       gate: "STRING_VALUE", // required
 * //       code: "STRING_VALUE", // required
 * //       message: "STRING_VALUE", // required
 * //       details: "DOCUMENT_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param RollbackOntologyCommandInput - {@link RollbackOntologyCommandInput}
 * @returns {@link RollbackOntologyCommandOutput}
 * @see {@link RollbackOntologyCommandInput} for command's `input` shape.
 * @see {@link RollbackOntologyCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Plan a pointer-only rollback
 * ```javascript
 * //
 * const input = {
 *   mode: "POINTER_ONLY",
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   ontologyId: "https://example.com/ontology/core",
 *   planOnly: true,
 *   targetVersionId: "ont-1a2b3c4d5e6f"
 * };
 * const command = new RollbackOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   mode: "POINTER_ONLY",
 *   target: {
 *     id: "ont-1a2b3c4d5e6f",
 *     semver: "1.0.0",
 *     status: "superseded"
 *   },
 *   targetTriples: 1280,
 *   targetVersionId: "ont-1a2b3c4d5e6f",
 *   wouldChangePointer: true
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RollbackOntologyCommand extends $Command
  .classBuilder<
    RollbackOntologyCommandInput,
    RollbackOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RollbackOntology", {})
  .n("ControlPlaneServiceClient", "RollbackOntologyCommand")
  .sc(RollbackOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RollbackOntologyInput;
      output: OntologyRollbackResult;
    };
    sdk: {
      input: RollbackOntologyCommandInput;
      output: RollbackOntologyCommandOutput;
    };
  };
}
