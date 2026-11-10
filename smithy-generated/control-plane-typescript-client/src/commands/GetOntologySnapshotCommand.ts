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
import type { GetOntologySnapshotInput, GetOntologySnapshotOutput } from "../models/models_0";
import { GetOntologySnapshot$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetOntologySnapshotCommand}.
 */
export interface GetOntologySnapshotCommandInput extends GetOntologySnapshotInput {}
/**
 * @public
 *
 * The output of {@link GetOntologySnapshotCommand}.
 */
export interface GetOntologySnapshotCommandOutput extends GetOntologySnapshotOutput, __MetadataBearer {}

/**
 * Read-only T-Box/A-Box coverage for the health board.
 *
 * Counts are SPARQL aggregations over the namespace's named graphs: the
 * T-Box is every ``owl:Class``/``owl:*Property`` declared in any of them,
 * the A-Box is every distinct subject typed by one of those classes. Classes
 * with zero instances are real gaps here, not hidden by a synthetic sample.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetOntologySnapshotCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetOntologySnapshotCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetOntologySnapshotInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new GetOntologySnapshotCommand(input);
 * const response = await client.send(command);
 * // { // GetOntologySnapshotOutput
 * //   tbox: { // OntologySnapshotTbox
 * //     classes: Number("int"), // required
 * //     objectProperties: Number("int"), // required
 * //     datatypeProperties: Number("int"), // required
 * //   },
 * //   abox: { // OntologySnapshotAbox
 * //     instances: Number("int"), // required
 * //     classesWithInstances: Number("int"), // required
 * //   },
 * //   coverage: { // OntologyCoverage
 * //     classCoverage: Number("double"), // required
 * //     unlabeledClasses: Number("int"), // required
 * //   },
 * //   graphs: [ // GraphUriList // required
 * //     "STRING_VALUE",
 * //   ],
 * //   source: "STRING_VALUE", // required
 * //   sampledAt: "STRING_VALUE", // required
 * // };
 *
 * ```
 *
 * @param GetOntologySnapshotCommandInput - {@link GetOntologySnapshotCommandInput}
 * @returns {@link GetOntologySnapshotCommandOutput}
 * @see {@link GetOntologySnapshotCommandInput} for command's `input` shape.
 * @see {@link GetOntologySnapshotCommandOutput} for command's `response` shape.
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
 * @example Read T-Box/A-Box coverage for a namespace
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new GetOntologySnapshotCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   abox: {
 *     classesWithInstances: 4,
 *     instances: 18020
 *   },
 *   coverage: {
 *     classCoverage: 0.0256,
 *     unlabeledClasses: 0
 *   },
 *   graphs: [
 *     "http://coa.amazon.com/onto/sales-crm",
 *     "urn:coa:abox:platform-synthetic"
 *   ],
 *   sampledAt: "2026-11-10T09:00:00Z",
 *   source: "SPARQL aggregation over the namespace named graphs",
 *   tbox: {
 *     classes: 156,
 *     datatypeProperties: 45,
 *     objectProperties: 84
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetOntologySnapshotCommand extends $Command
  .classBuilder<
    GetOntologySnapshotCommandInput,
    GetOntologySnapshotCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetOntologySnapshot", {})
  .n("ControlPlaneServiceClient", "GetOntologySnapshotCommand")
  .sc(GetOntologySnapshot$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetOntologySnapshotInput;
      output: GetOntologySnapshotOutput;
    };
    sdk: {
      input: GetOntologySnapshotCommandInput;
      output: GetOntologySnapshotCommandOutput;
    };
  };
}
