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
import type { ListAnswerQualityRunsInput, ListAnswerQualityRunsOutput } from "../models/models_1";
import { ListAnswerQualityRuns$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListAnswerQualityRunsCommand}.
 */
export interface ListAnswerQualityRunsCommandInput extends ListAnswerQualityRunsInput {}
/**
 * @public
 *
 * The output of {@link ListAnswerQualityRunsCommand}.
 */
export interface ListAnswerQualityRunsCommandOutput extends ListAnswerQualityRunsOutput, __MetadataBearer {}

/**
 * List stored golden-set runs, newest first by `ran_at`.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListAnswerQualityRunsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListAnswerQualityRunsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListAnswerQualityRunsInput
 *   limit: Number("int"),
 *   strategy: "lexical" || "vector" || "hybrid",
 *   since: new Date("TIMESTAMP"),
 * };
 * const command = new ListAnswerQualityRunsCommand(input);
 * const response = await client.send(command);
 * // { // ListAnswerQualityRunsOutput
 * //   items: [ // AnswerQualityRunList // required
 * //     { // AnswerQualityRun
 * //       runId: "STRING_VALUE", // required
 * //       ranAt: new Date("TIMESTAMP"), // required
 * //       strategy: "lexical" || "vector" || "hybrid", // required
 * //       goldenSet: "STRING_VALUE", // required
 * //       evaluated: Number("int"), // required
 * //       passed: Number("int"), // required
 * //       failed: Number("int"), // required
 * //       passRate: Number("float"), // required
 * //       citationCoverageRate: Number("float"), // required
 * //       citationResolvableRate: Number("float"), // required
 * //       brokenLinkRate: Number("float"), // required
 * //       regression: true || false, // required
 * //       layerCoverage: [ // QualityLayerCoverageList
 * //         { // QualityLayerCoverage
 * //           layer: "STRING_VALUE", // required
 * //           covered: Number("int"), // required
 * //           evaluated: Number("int"), // required
 * //           rate: Number("float"), // required
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   totalCount: Number("long"), // required
 * //   limit: Number("int"), // required
 * //   strategy: "lexical" || "vector" || "hybrid",
 * //   since: new Date("TIMESTAMP"),
 * //   readOnly: true || false, // required
 * // };
 *
 * ```
 *
 * @param ListAnswerQualityRunsCommandInput - {@link ListAnswerQualityRunsCommandInput}
 * @returns {@link ListAnswerQualityRunsCommandOutput}
 * @see {@link ListAnswerQualityRunsCommandInput} for command's `input` shape.
 * @see {@link ListAnswerQualityRunsCommandOutput} for command's `response` shape.
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
 * @example Two stored runs with layer coverage
 * ```javascript
 * //
 * const input = {
 *   limit: 2,
 *   strategy: "lexical"
 * };
 * const command = new ListAnswerQualityRunsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       brokenLinkRate: 0.0,
 *       citationCoverageRate: 1.0,
 *       citationResolvableRate: 1.0,
 *       evaluated: 10,
 *       failed: 3,
 *       goldenSet: "r02-golden-10",
 *       layerCoverage: [
 *         {
 *           covered: 10,
 *           evaluated: 10,
 *           layer: "ontology",
 *           rate: 1.0
 *         },
 *         {
 *           covered: 8,
 *           evaluated: 10,
 *           layer: "terms",
 *           rate: 0.8
 *         },
 *         {
 *           covered: 6,
 *           evaluated: 10,
 *           layer: "metrics",
 *           rate: 0.6
 *         },
 *         {
 *           covered: 2,
 *           evaluated: 10,
 *           layer: "facts",
 *           rate: 0.2
 *         }
 *       ],
 *       passRate: 0.7,
 *       passed: 7,
 *       ranAt: "2026-11-10T12:40:00Z",
 *       regression: false,
 *       runId: "aq-3f9c2b7d1e4a",
 *       strategy: "lexical"
 *     },
 *     {
 *       brokenLinkRate: 0.0,
 *       citationCoverageRate: 1.0,
 *       citationResolvableRate: 1.0,
 *       evaluated: 10,
 *       failed: 3,
 *       goldenSet: "r02-golden-10",
 *       passRate: 0.7,
 *       passed: 7,
 *       ranAt: "2026-11-10T12:20:00Z",
 *       regression: false,
 *       runId: "aq-1a2b3c4d5e6f",
 *       strategy: "lexical"
 *     }
 *   ],
 *   limit: 2,
 *   readOnly: true,
 *   totalCount: 2
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListAnswerQualityRunsCommand extends $Command
  .classBuilder<
    ListAnswerQualityRunsCommandInput,
    ListAnswerQualityRunsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListAnswerQualityRuns", {})
  .n("ControlPlaneServiceClient", "ListAnswerQualityRunsCommand")
  .sc(ListAnswerQualityRuns$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListAnswerQualityRunsInput;
      output: ListAnswerQualityRunsOutput;
    };
    sdk: {
      input: ListAnswerQualityRunsCommandInput;
      output: ListAnswerQualityRunsCommandOutput;
    };
  };
}
