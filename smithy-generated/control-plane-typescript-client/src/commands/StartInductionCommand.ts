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
import type { StartInductionInput, StartInductionOutput } from "../models/models_0";
import { StartInduction$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link StartInductionCommand}.
 */
export interface StartInductionCommandInput extends StartInductionInput {}
/**
 * @public
 *
 * The output of {@link StartInductionCommand}.
 */
export interface StartInductionCommandOutput extends StartInductionOutput, __MetadataBearer {}

/**
 * Start an ontology induction job from one or more data sources.
 * Returns immediately with a job ID; induction runs asynchronously.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, StartInductionCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, StartInductionCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // StartInductionInput
 *   namespaceId: "STRING_VALUE", // required
 *   datasourceIds: [ // DataSourceIdList // required
 *     "STRING_VALUE",
 *   ],
 *   ontologyUriPrefix: "STRING_VALUE", // required
 *   label: "STRING_VALUE",
 *   confidenceThreshold: Number("float"),
 *   rerankMaxTokens: Number("int"),
 *   strategy: "table_to_ontology" || "rigor_ontology" || "unstructured_lexical_graph" || "bridge_to_tables",
 *   bridgeOptions: { // BridgeOptions
 *     maxTables: Number("int"),
 *     concurrency: Number("int"),
 *     dryRun: true || false,
 *   },
 *   groundingOntologyIds: [ // GroundingOntologyIdList
 *     "STRING_VALUE",
 *   ],
 *   groundingMode: "NONE" || "STANDARD" || "ENHANCED",
 *   graphArn: "STRING_VALUE",
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new StartInductionCommand(input);
 * const response = await client.send(command);
 * // { // StartInductionOutput
 * //   jobId: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param StartInductionCommandInput - {@link StartInductionCommandInput}
 * @returns {@link StartInductionCommandOutput}
 * @see {@link StartInductionCommandInput} for command's `input` shape.
 * @see {@link StartInductionCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Induce an ontology from two sales data sources
 * ```javascript
 * //
 * const input = {
 *   confidenceThreshold: 0.75,
 *   datasourceIds: [
 *     "orders_db",
 *     "customers_db"
 *   ],
 *   groundingMode: "ENHANCED",
 *   groundingOntologyIds: [
 *     "schema-org-core"
 *   ],
 *   label: "Sales catalog induction",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyUriPrefix: "https://ontology.example.com/sales/",
 *   strategy: "table_to_ontology"
 * };
 * const command = new StartInductionCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   jobId: "3f8a1c2d-9b4e-4a6f-8c1d-2e5f7a9b0c3d"
 * }
 * *\/
 * ```
 *
 * @example Preview the document-to-table bridge on an accepted ontology
 * ```javascript
 * //
 * const input = {
 *   bridgeOptions: {
 *     dryRun: true,
 *     maxTables: 20
 *   },
 *   datasourceIds:   [],
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   ontologyUriPrefix: "https://ontology.example.com/sales#",
 *   strategy: "bridge_to_tables"
 * };
 * const command = new StartInductionCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   jobId: "7c2e4b1a-5d3f-4e8a-9b6c-1a2b3c4d5e6f"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class StartInductionCommand extends $Command
  .classBuilder<
    StartInductionCommandInput,
    StartInductionCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "StartInduction", {})
  .n("ControlPlaneServiceClient", "StartInductionCommand")
  .sc(StartInduction$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: StartInductionInput;
      output: StartInductionOutput;
    };
    sdk: {
      input: StartInductionCommandInput;
      output: StartInductionCommandOutput;
    };
  };
}
