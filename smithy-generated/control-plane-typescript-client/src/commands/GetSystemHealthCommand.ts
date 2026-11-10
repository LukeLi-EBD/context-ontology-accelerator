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
import type { GetSystemHealthOutput } from "../models/models_0";
import { GetSystemHealth$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetSystemHealthCommand}.
 */
export interface GetSystemHealthCommandInput {}
/**
 * @public
 *
 * The output of {@link GetSystemHealthCommand}.
 */
export interface GetSystemHealthCommandOutput extends GetSystemHealthOutput, __MetadataBearer {}

/**
 * Report the aggregate health of the platform's downstream dependencies.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetSystemHealthCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetSystemHealthCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = {};
 * const command = new GetSystemHealthCommand(input);
 * const response = await client.send(command);
 * // { // GetSystemHealthOutput
 * //   status: "STRING_VALUE", // required
 * //   ontologyInduction: { // OntologyInductionHealth
 * //     graphStore: "STRING_VALUE",
 * //     vectorStore: "STRING_VALUE",
 * //     bedrockEmbeddings: "STRING_VALUE",
 * //     descriptionLlm: "STRING_VALUE",
 * //   },
 * //   dynamodb: "STRING_VALUE",
 * //   neptuneKg: "STRING_VALUE",
 * //   opensearch: "STRING_VALUE",
 * //   schemaVersion: { // SystemSchemaVersion
 * //     codeVersion: Number("int"), // required
 * //     dbVersion: Number("int"),
 * //     consistent: true || false,
 * //     source: "STRING_VALUE", // required
 * //   },
 * // };
 *
 * ```
 *
 * @param GetSystemHealthCommandInput - {@link GetSystemHealthCommandInput}
 * @returns {@link GetSystemHealthCommandOutput}
 * @see {@link GetSystemHealthCommandInput} for command's `input` shape.
 * @see {@link GetSystemHealthCommandOutput} for command's `response` shape.
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
 * @example All subsystems healthy
 * ```javascript
 * //
 * const input = { /* empty *\/ };
 * const command = new GetSystemHealthCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   dynamodb: "ok",
 *   neptuneKg: "ok",
 *   ontologyInduction: {
 *     bedrockEmbeddings: "ok",
 *     descriptionLlm: "ok",
 *     graphStore: "ok",
 *     vectorStore: "ok"
 *   },
 *   opensearch: "ok",
 *   status: "ok"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetSystemHealthCommand extends $Command
  .classBuilder<
    GetSystemHealthCommandInput,
    GetSystemHealthCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetSystemHealth", {})
  .n("ControlPlaneServiceClient", "GetSystemHealthCommand")
  .sc(GetSystemHealth$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: {};
      output: GetSystemHealthOutput;
    };
    sdk: {
      input: GetSystemHealthCommandInput;
      output: GetSystemHealthCommandOutput;
    };
  };
}
