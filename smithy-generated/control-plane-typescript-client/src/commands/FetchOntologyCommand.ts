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
import type { FetchOntologyInput, FetchOntologyOutput } from "../models/models_0";
import { FetchOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link FetchOntologyCommand}.
 */
export interface FetchOntologyCommandInput extends FetchOntologyInput {}
/**
 * @public
 *
 * The output of {@link FetchOntologyCommand}.
 */
export interface FetchOntologyCommandOutput extends FetchOntologyOutput, __MetadataBearer {}

/**
 * Fetch an ontology from its source URL and ingest it.
 *
 * Naturally idempotent, so there is no `clientToken`: it refreshes an ontology
 * that must already be registered under `ontologyId` (404 otherwise), and a
 * repeat re-fetches into the same registry row instead of creating another.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, FetchOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, FetchOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // FetchOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 *   sourceUrl: "STRING_VALUE",
 * };
 * const command = new FetchOntologyCommand(input);
 * const response = await client.send(command);
 * // { // FetchOntologyOutput
 * //   result: "DOCUMENT_VALUE", // required
 * // };
 *
 * ```
 *
 * @param FetchOntologyCommandInput - {@link FetchOntologyCommandInput}
 * @returns {@link FetchOntologyCommandOutput}
 * @see {@link FetchOntologyCommandInput} for command's `input` shape.
 * @see {@link FetchOntologyCommandOutput} for command's `response` shape.
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
 * @example Fetch a foundational ontology from a URL
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "foaf",
 *   sourceUrl: "https://xmlns.com/foaf/spec/index.rdf"
 * };
 * const command = new FetchOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   result: {
 *     classCount: 13,
 *     ontologyId: "foaf",
 *     status: "ingested"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class FetchOntologyCommand extends $Command
  .classBuilder<
    FetchOntologyCommandInput,
    FetchOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "FetchOntology", {})
  .n("ControlPlaneServiceClient", "FetchOntologyCommand")
  .sc(FetchOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: FetchOntologyInput;
      output: FetchOntologyOutput;
    };
    sdk: {
      input: FetchOntologyCommandInput;
      output: FetchOntologyCommandOutput;
    };
  };
}
