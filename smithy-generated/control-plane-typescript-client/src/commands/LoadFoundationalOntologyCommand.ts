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
import type { LoadFoundationalOntologyInput, LoadFoundationalOntologyOutput } from "../models/models_1";
import { LoadFoundationalOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link LoadFoundationalOntologyCommand}.
 */
export interface LoadFoundationalOntologyCommandInput extends LoadFoundationalOntologyInput {}
/**
 * @public
 *
 * The output of {@link LoadFoundationalOntologyCommand}.
 */
export interface LoadFoundationalOntologyCommandOutput extends LoadFoundationalOntologyOutput, __MetadataBearer {}

/**
 * Trigger loading/embedding of a foundational ontology into the namespace.
 * Each call starts a new load job; send a `clientToken` to make a retry safe.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, LoadFoundationalOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, LoadFoundationalOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // LoadFoundationalOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   key: "STRING_VALUE", // required
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new LoadFoundationalOntologyCommand(input);
 * const response = await client.send(command);
 * // { // LoadFoundationalOntologyOutput
 * //   status: "STRING_VALUE", // required
 * //   ontologyId: "STRING_VALUE",
 * //   classCount: Number("int"),
 * //   embeddingCount: Number("int"),
 * // };
 *
 * ```
 *
 * @param LoadFoundationalOntologyCommandInput - {@link LoadFoundationalOntologyCommandInput}
 * @returns {@link LoadFoundationalOntologyCommandOutput}
 * @see {@link LoadFoundationalOntologyCommandInput} for command's `input` shape.
 * @see {@link LoadFoundationalOntologyCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
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
 * @example Load a foundational ontology into a namespace
 * ```javascript
 * //
 * const input = {
 *   key: "schema-org-core",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new LoadFoundationalOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   classCount: 843,
 *   embeddingCount: 843,
 *   ontologyId: "schema-org-core",
 *   status: "loading"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class LoadFoundationalOntologyCommand extends $Command
  .classBuilder<
    LoadFoundationalOntologyCommandInput,
    LoadFoundationalOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "LoadFoundationalOntology", {})
  .n("ControlPlaneServiceClient", "LoadFoundationalOntologyCommand")
  .sc(LoadFoundationalOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: LoadFoundationalOntologyInput;
      output: LoadFoundationalOntologyOutput;
    };
    sdk: {
      input: LoadFoundationalOntologyCommandInput;
      output: LoadFoundationalOntologyCommandOutput;
    };
  };
}
