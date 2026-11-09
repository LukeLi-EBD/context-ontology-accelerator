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
import type { GetOntologyInput, GetOntologyOutput } from "../models/models_0";
import { GetOntology$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologyCommand}.
 */
export interface GetOntologyCommandInput extends GetOntologyInput {}
/**
 * @public
 *
 * The output of {@link GetOntologyCommand}.
 */
export interface GetOntologyCommandOutput extends GetOntologyOutput, __MetadataBearer {}

/**
 * Get a single ontology by ID.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologyCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologyCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologyInput
 *   namespaceId: "STRING_VALUE", // required
 *   ontologyId: "STRING_VALUE", // required
 * };
 * const command = new GetOntologyCommand(input);
 * const response = await client.send(command);
 * // { // GetOntologyOutput
 * //   ontology: "DOCUMENT_VALUE", // required
 * // };
 *
 * ```
 *
 * @param GetOntologyCommandInput - {@link GetOntologyCommandInput}
 * @returns {@link GetOntologyCommandOutput}
 * @see {@link GetOntologyCommandInput} for command's `input` shape.
 * @see {@link GetOntologyCommandOutput} for command's `response` shape.
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
 * @example Get an ontology by ID
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyId: "01J9ZQ8XN4T7VBR6C2K9YHMED0"
 * };
 * const command = new GetOntologyCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   ontology: {
 *     classCount: 12,
 *     ontologyId: "http://coa.amazon.com/onto/sales-crm",
 *     ontologyType: "induced",
 *     title: "Sales CRM",
 *     uri: "http://coa.amazon.com/onto/sales-crm"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologyCommand extends $Command
  .classBuilder<
    GetOntologyCommandInput,
    GetOntologyCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntology", {})
  .n("ControlPlaneServiceClient", "GetOntologyCommand")
  .sc(GetOntology$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologyInput;
      output: GetOntologyOutput;
    };
    sdk: {
      input: GetOntologyCommandInput;
      output: GetOntologyCommandOutput;
    };
  };
}
