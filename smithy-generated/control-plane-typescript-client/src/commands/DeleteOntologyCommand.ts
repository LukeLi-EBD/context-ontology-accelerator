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
import type { DeleteOntologyInput } from "../models/models_0";
import { DeleteOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteOntologyCommand}.
 */
export interface DeleteOntologyCommandInput extends DeleteOntologyInput {}
/**
 * @public
 *
 * The output of {@link DeleteOntologyCommand}.
 */
export interface DeleteOntologyCommandOutput extends __MetadataBearer {}

/**
 * Delete an induced ontology and all its artifacts (graph triples,
 * vector embeddings, and registry entry) from a namespace.
 *
 * Async — returns **202** immediately: the registry entry is removed
 * synchronously (so ``ListOntologies`` no longer lists it — the client-visible
 * status), then the slower Neptune named-graph DROP and per-embedding AOSS
 * teardown run in the background. Clients poll ``ListOntologies`` until the id
 * is gone. This mirrors the async accept flow and avoids the API Gateway 29s
 * integration timeout (504) on large ontologies.
 *
 * The ontology id is a full IRI (contains ``://`` and ``#``), so it is passed
 * as a query parameter rather than a path label — API Gateway mangles a
 * URL-encoded ``#`` in a path segment (falls through to IAM auth → 403). This
 * mirrors the graph vertex-lookup endpoints (``/graph/class?uri=``).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, DeleteOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, DeleteOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // DeleteOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 * };
 * const command = new DeleteOntologyCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteOntologyCommandInput - {@link DeleteOntologyCommandInput}
 * @returns {@link DeleteOntologyCommandOutput}
 * @see {@link DeleteOntologyCommandInput} for command's `input` shape.
 * @see {@link DeleteOntologyCommandOutput} for command's `response` shape.
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
 * @example Delete an induced ontology (async, 202)
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "http://coa.amazon.com/onto/sales-crm"
 * };
 * const command = new DeleteOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* empty *\/ }
 * *\/
 * ```
 *
 * @public
 */
export class DeleteOntologyCommand extends $Command
  .classBuilder<
    DeleteOntologyCommandInput,
    DeleteOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "DeleteOntology", {})
  .n("ControlPlaneServiceClient", "DeleteOntologyCommand")
  .sc(DeleteOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: DeleteOntologyInput;
      output: {};
    };
    sdk: {
      input: DeleteOntologyCommandInput;
      output: DeleteOntologyCommandOutput;
    };
  };
}
