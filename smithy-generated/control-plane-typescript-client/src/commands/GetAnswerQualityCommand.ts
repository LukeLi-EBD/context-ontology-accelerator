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
import type { AnswerQualityResponse, GetAnswerQualityInput } from "../models/models_1";
import { GetAnswerQuality$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetAnswerQualityCommand}.
 */
export interface GetAnswerQualityCommandInput extends GetAnswerQualityInput {}
/**
 * @public
 *
 * The output of {@link GetAnswerQualityCommand}.
 */
export interface GetAnswerQualityCommandOutput extends AnswerQualityResponse, __MetadataBearer {}

/**
 * Run the answer-quality golden set.
 *
 * The endpoint is read-only. `limit` caps the number of per-case details
 * returned; rates are still computed over the whole set.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, GetAnswerQualityCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, GetAnswerQualityCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // GetAnswerQualityInput
 *   strategy: "lexical" || "vector" || "hybrid", // required
 *   limit: Number("int"),
 * };
 * const command = new GetAnswerQualityCommand(input);
 * const response = await client.send(command);
 * // { // AnswerQualityResponse
 * //   strategy: "STRING_VALUE", // required
 * //   goldenSet: { // AnswerQualityGoldenSet
 * //     id: "STRING_VALUE", // required
 * //     count: Number("int"), // required
 * //     evaluated: Number("int"), // required
 * //     caseId: "STRING_VALUE",
 * //   },
 * //   summary: { // AnswerQualitySummary
 * //     cases: Number("int"), // required
 * //     passed: Number("int"), // required
 * //     failed: Number("int"), // required
 * //     passRate: Number("double"), // required
 * //     casesWithCitations: Number("int"), // required
 * //     citationCoverageRate: Number("double"), // required
 * //     citations: Number("int"), // required
 * //     resolvableCitations: Number("int"), // required
 * //     citationResolvableRate: Number("double"), // required
 * //     brokenLinkRate: Number("double"), // required
 * //     baselineBrokenLinkRate: Number("double"), // required
 * //     regression: true || false, // required
 * //   },
 * //   citationCoverageByType: [ // AnswerQualityByTypeList
 * //     { // AnswerQualityByType
 * //       type: "STRING_VALUE", // required
 * //       cases: Number("int"), // required
 * //       refused: Number("int"), // required
 * //       withCitations: Number("int"),
 * //       citations: Number("int"), // required
 * //       resolvable: Number("int"),
 * //       citationCoverageRate: Number("double"), // required
 * //       resolvableRate: Number("double"),
 * //       refusalRate: Number("double"),
 * //     },
 * //   ],
 * //   refusalsByReason: [ // AnswerQualityRefusalReasonList
 * //     { // AnswerQualityRefusalReason
 * //       type: "STRING_VALUE", // required
 * //       reasonCode: "STRING_VALUE", // required
 * //       count: Number("int"), // required
 * //     },
 * //   ],
 * //   refusalsByType: [
 * //     {
 * //       type: "STRING_VALUE", // required
 * //       cases: Number("int"), // required
 * //       refused: Number("int"), // required
 * //       withCitations: Number("int"),
 * //       citations: Number("int"), // required
 * //       resolvable: Number("int"),
 * //       citationCoverageRate: Number("double"), // required
 * //       resolvableRate: Number("double"),
 * //       refusalRate: Number("double"),
 * //     },
 * //   ],
 * //   refusalsWithoutLayers: [ // DocumentList
 * //     "DOCUMENT_VALUE",
 * //   ],
 * //   brokenLinks: [
 * //     "DOCUMENT_VALUE",
 * //   ],
 * //   cases: [ // AnswerQualityCaseList // required
 * //     { // AnswerQualityCase
 * //       id: "STRING_VALUE", // required
 * //       query: "STRING_VALUE", // required
 * //       type: "STRING_VALUE", // required
 * //       expectRefused: true || false, // required
 * //       actual: { // AnswerQualityActual
 * //         refused: true || false, // required
 * //         answerType: "STRING_VALUE", // required
 * //         answerMode: "STRING_VALUE", // required
 * //         reasonCode: "STRING_VALUE",
 * //         degraded: true || false, // required
 * //         citations: [ // AnswerQualityCitationList // required
 * //           { // AnswerQualityCitation
 * //             id: "STRING_VALUE", // required
 * //             kind: "STRING_VALUE", // required
 * //             ref: "STRING_VALUE", // required
 * //             versionId: "STRING_VALUE",
 * //             resolveUrl: "STRING_VALUE",
 * //             resolvable: true || false, // required
 * //           },
 * //         ],
 * //         citationKinds: [ // StringList // required
 * //           "STRING_VALUE",
 * //         ],
 * //         missingLayers: [ // required
 * //           "STRING_VALUE",
 * //         ],
 * //       },
 * //       pass: true || false, // required
 * //       failures: [ // required
 * //         "STRING_VALUE",
 * //       ],
 * //       drillDownUrl: "STRING_VALUE",
 * //     },
 * //   ],
 * //   empty: true || false, // required
 * //   emptyReason: "STRING_VALUE",
 * //   readOnly: true || false, // required
 * // };
 *
 * ```
 *
 * @param GetAnswerQualityCommandInput - {@link GetAnswerQualityCommandInput}
 * @returns {@link GetAnswerQualityCommandOutput}
 * @see {@link GetAnswerQualityCommandInput} for command's `input` shape.
 * @see {@link GetAnswerQualityCommandOutput} for command's `response` shape.
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
 * @example Run the lexical golden set
 * ```javascript
 * //
 * const input = {
 *   limit: 10,
 *   strategy: "lexical"
 * };
 * const command = new GetAnswerQualityCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   brokenLinks: [
 *     {
 *       citationId: "cit-9",
 *       ref: "doc-missing"
 *     }
 *   ],
 *   cases: [
 *     {
 *       actual: {
 *         answerMode: "strict",
 *         answerType: "graph",
 *         citationKinds: [
 *           "fact"
 *         ],
 *         citations: [
 *           {
 *             id: "cit-1",
 *             kind: "fact",
 *             ref: "fact-1a2b3c4d5e6f",
 *             resolvable: true
 *           }
 *         ],
 *         degraded: false,
 *         missingLayers:         [],
 *         refused: false
 *       },
 *       drillDownUrl: "/answer?q=case-001",
 *       expectRefused: false,
 *       failures:       [],
 *       id: "case-001",
 *       pass: true,
 *       query: "Contract Ledger 属于哪个域？",
 *       type: "entity"
 *     }
 *   ],
 *   citationCoverageByType: [
 *     {
 *       cases: 4,
 *       citationCoverageRate: 1.0,
 *       citations: 6,
 *       refused: 0,
 *       resolvable: 6,
 *       resolvableRate: 1.0,
 *       type: "entity",
 *       withCitations: 4
 *     }
 *   ],
 *   empty: false,
 *   goldenSet: {
 *     count: 12,
 *     evaluated: 12,
 *     id: "golden-v1"
 *   },
 *   readOnly: true,
 *   refusalsByReason: [
 *     {
 *       count: 1,
 *       reasonCode: "E_NO_EVIDENCE",
 *       type: "out-of-scope"
 *     }
 *   ],
 *   refusalsByType:   [],
 *   refusalsWithoutLayers:   [],
 *   strategy: "lexical",
 *   summary: {
 *     baselineBrokenLinkRate: 0.06,
 *     brokenLinkRate: 0.0556,
 *     cases: 12,
 *     casesWithCitations: 10,
 *     citationCoverageRate: 0.8333,
 *     citationResolvableRate: 0.9444,
 *     citations: 18,
 *     failed: 1,
 *     passRate: 0.9167,
 *     passed: 11,
 *     regression: false,
 *     resolvableCitations: 17
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class GetAnswerQualityCommand extends $Command
  .classBuilder<
    GetAnswerQualityCommandInput,
    GetAnswerQualityCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "GetAnswerQuality", {})
  .n("ControlPlaneServiceClient", "GetAnswerQualityCommand")
  .sc(GetAnswerQuality$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: GetAnswerQualityInput;
      output: AnswerQualityResponse;
    };
    sdk: {
      input: GetAnswerQualityCommandInput;
      output: GetAnswerQualityCommandOutput;
    };
  };
}
