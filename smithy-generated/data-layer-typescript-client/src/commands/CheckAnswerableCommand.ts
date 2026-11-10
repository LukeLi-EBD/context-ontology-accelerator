// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  DataLayerServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../DataLayerServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { CheckAnswerableInput, CheckAnswerableOutput } from "../models/models_0";
import { CheckAnswerable$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CheckAnswerableCommand}.
 */
export interface CheckAnswerableCommandInput extends CheckAnswerableInput {}
/**
 * @public
 *
 * The output of {@link CheckAnswerableCommand}.
 */
export interface CheckAnswerableCommandOutput extends CheckAnswerableOutput, __MetadataBearer {}

/**
 * Pre-check whether an ontology can answer a question, reporting coverage for
 * each of the four layers (ontology, terms, metrics, facts) and, for every
 * gap, what is missing and how to fix it.
 *
 * Read-only. A layer whose inputs are not available reports status
 * `unavailable` (or `not_applicable`) and no coverage value; it is never
 * silently reported as zero coverage.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { DataLayerServiceClient, CheckAnswerableCommand } from "@coa/data-layer-client"; // ES Modules import
 * // const { DataLayerServiceClient, CheckAnswerableCommand } = require("@coa/data-layer-client"); // CommonJS import
 * // import type { DataLayerServiceClientConfig } from "@coa/data-layer-client";
 * const config = {}; // type is DataLayerServiceClientConfig
 * const client = new DataLayerServiceClient(config);
 * const input = { // CheckAnswerableInput
 *   namespaceId: "STRING_VALUE", // required
 *   query: "STRING_VALUE", // required
 *   ontologyVersion: "STRING_VALUE",
 *   minCoverage: Number("float"),
 * };
 * const command = new CheckAnswerableCommand(input);
 * const response = await client.send(command);
 * // { // CheckAnswerableOutput
 * //   query: "STRING_VALUE", // required
 * //   answerable: true || false, // required
 * //   valueAnswerable: true || false, // required
 * //   answerMode: "STRING_VALUE", // required
 * //   intent: "STRING_VALUE", // required
 * //   degraded: true || false, // required
 * //   coverage: Number("float"), // required
 * //   threshold: Number("float"), // required
 * //   coverageChars: { // CoverageChars
 * //     covered: Number("int"), // required
 * //     total: Number("int"), // required
 * //   },
 * //   ontologyVersion: "STRING_VALUE", // required
 * //   ontologyGraph: "STRING_VALUE", // required
 * //   termSource: "STRING_VALUE", // required
 * //   termCount: Number("int"), // required
 * //   matchedTerms: [ // MatchedTermList // required
 * //     { // MatchedTerm
 * //       term: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       span: [ // Span // required
 * //         Number("int"),
 * //       ],
 * //     },
 * //   ],
 * //   layers: [ // CoverageLayerList // required
 * //     { // CoverageLayer
 * //       layer: "STRING_VALUE", // required
 * //       status: "STRING_VALUE", // required
 * //       coverage: Number("float"),
 * //       matched: [ // LayerMatchList // required
 * //         { // LayerMatch
 * //           id: "STRING_VALUE",
 * //           label: "STRING_VALUE",
 * //           predicate: "STRING_VALUE",
 * //           source: "STRING_VALUE",
 * //           score: Number("float"),
 * //           metricId: "STRING_VALUE",
 * //           status: "STRING_VALUE",
 * //           code: "STRING_VALUE",
 * //           observationRows: Number("int"),
 * //           factFunction: "STRING_VALUE",
 * //         },
 * //       ],
 * //       missing: [ // StringList // required
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * //   missing: [ // MissingGapList // required
 * //     { // MissingGap
 * //       layer: "STRING_VALUE", // required
 * //       code: "STRING_VALUE", // required
 * //       text: "STRING_VALUE",
 * //       span: [
 * //         Number("int"),
 * //       ],
 * //       what: "STRING_VALUE",
 * //       howToFix: "STRING_VALUE",
 * //       metricId: "STRING_VALUE",
 * //       nearbyTerms: [ // NearbyTermList
 * //         { // NearbyTerm
 * //           term: "STRING_VALUE", // required
 * //           label: "STRING_VALUE", // required
 * //           similarity: Number("float"), // required
 * //         },
 * //       ],
 * //       candidates: [ // GapCandidateList
 * //         { // GapCandidate
 * //           id: "STRING_VALUE", // required
 * //           label: "STRING_VALUE", // required
 * //           score: Number("float"), // required
 * //         },
 * //       ],
 * //     },
 * //   ],
 * //   candidates: [ // AnswerCandidateList // required
 * //     { // AnswerCandidate
 * //       layer: "STRING_VALUE", // required
 * //       id: "STRING_VALUE", // required
 * //       label: "STRING_VALUE", // required
 * //       reason: "STRING_VALUE", // required
 * //       score: Number("float"), // required
 * //     },
 * //   ],
 * //   reasons: [ // required
 * //     "STRING_VALUE",
 * //   ],
 * //   reasonCode: "STRING_VALUE",
 * //   hint: "STRING_VALUE",
 * //   timings: { // AnswerTimings
 * //     termsMs: Number("int"), // required
 * //     metricMs: Number("int"), // required
 * //     factsMs: Number("int"), // required
 * //   },
 * // };
 *
 * ```
 *
 * @param CheckAnswerableCommandInput - {@link CheckAnswerableCommandInput}
 * @returns {@link CheckAnswerableCommandOutput}
 * @see {@link CheckAnswerableCommandInput} for command's `input` shape.
 * @see {@link CheckAnswerableCommandOutput} for command's `response` shape.
 * @see {@link DataLayerServiceClientResolvedConfig | config} for DataLayerServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link AccessDeniedError} (client fault)
 *  Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
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
 * @throws {@link RateLimitExceededError} (client fault)
 *  Returned with HTTP 429 when the caller exceeds the request rate limit;
 * `retryAfterSeconds` indicates how long to wait before retrying.
 *
 * @throws {@link DataLayerServiceServiceException}
 * <p>Base exception class for all service exceptions from DataLayerService service.</p>
 *
 *
 * @example A value question that is fully covered
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd",
 *   query: "上个月华东区的销售额是多少？"
 * };
 * const command = new CheckAnswerableCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   answerMode: "value",
 *   answerable: true,
 *   candidates: [
 *     {
 *       id: "sales_amount",
 *       label: "销售额",
 *       layer: "metrics",
 *       reason: "exact_name",
 *       score: 0.98
 *     }
 *   ],
 *   coverage: 0.92,
 *   coverageChars: {
 *     covered: 23,
 *     total: 25
 *   },
 *   degraded: false,
 *   intent: "value",
 *   layers: [
 *     {
 *       coverage: 0.92,
 *       layer: "ontology",
 *       matched: [
 *         {
 *           id: "urn:coa:metric:sales_amount",
 *           label: "销售额",
 *           source: "rdfs:label"
 *         }
 *       ],
 *       missing:       [],
 *       status: "covered"
 *     },
 *     {
 *       coverage: 1.0,
 *       layer: "terms",
 *       matched: [
 *         {
 *           id: "urn:coa:term:east_china",
 *           label: "华东区",
 *           source: "skos"
 *         }
 *       ],
 *       missing:       [],
 *       status: "covered"
 *     },
 *     {
 *       coverage: 1.0,
 *       layer: "metrics",
 *       matched: [
 *         {
 *           id: "sales_amount",
 *           label: "销售额",
 *           score: 0.98
 *         }
 *       ],
 *       missing:       [],
 *       status: "covered"
 *     },
 *     {
 *       coverage: 1.0,
 *       layer: "facts",
 *       matched: [
 *         {
 *           code: "FACT_COVERED",
 *           metricId: "sales_amount",
 *           observationRows: 12,
 *           status: "covered"
 *         }
 *       ],
 *       missing:       [],
 *       status: "covered"
 *     }
 *   ],
 *   matchedTerms: [
 *     {
 *       label: "销售额",
 *       span: [
 *         0,
 *         3
 *       ],
 *       term: "urn:coa:metric:sales_amount"
 *     }
 *   ],
 *   missing:   [],
 *   ontologyGraph: "https://coa.local/graph/ed70a15c-2d42-4dc9-8c61-33b2584f05fd/urn%3Acoa%3Aontology%3Av3",
 *   ontologyVersion: "v3",
 *   query: "上个月华东区的销售额是多少？",
 *   reasons:   [],
 *   termCount: 148,
 *   termSource: "skos(prefLabel/altLabel) when present + rdfs:label baseline",
 *   threshold: 0.8,
 *   timings: {
 *     factsMs: 41,
 *     metricMs: 3,
 *     termsMs: 12
 *   },
 *   valueAnswerable: true
 * }
 * *\/
 * ```
 *
 * @example A question with gaps in the ontology and facts layers
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "ed70a15c-2d42-4dc9-8c61-33b2584f05fd",
 *   query: "上个季度供应商交货及时率是多少？"
 * };
 * const command = new CheckAnswerableCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   answerMode: "none",
 *   answerable: false,
 *   candidates: [
 *     {
 *       id: "on_time_delivery_rate",
 *       label: "交货及时率",
 *       layer: "metrics",
 *       reason: "fuzzy_name",
 *       score: 0.71
 *     }
 *   ],
 *   coverage: 0.55,
 *   coverageChars: {
 *     covered: 11,
 *     total: 20
 *   },
 *   degraded: true,
 *   hint: "本体未覆盖问题中的这些概念：供应商；请先补充术语（T-Box）或缩小问题范围",
 *   intent: "value",
 *   layers: [
 *     {
 *       coverage: 0.55,
 *       layer: "ontology",
 *       matched:       [],
 *       missing: [
 *         "供应商"
 *       ],
 *       status: "partial"
 *     },
 *     {
 *       coverage: 0.0,
 *       layer: "terms",
 *       matched:       [],
 *       missing: [
 *         "交货及时率"
 *       ],
 *       status: "missing"
 *     },
 *     {
 *       coverage: 0.0,
 *       layer: "metrics",
 *       matched:       [],
 *       missing: [
 *         "on_time_delivery_rate"
 *       ],
 *       status: "missing"
 *     },
 *     {
 *       layer: "facts",
 *       matched:       [],
 *       missing:       [],
 *       status: "not_applicable"
 *     }
 *   ],
 *   matchedTerms:   [],
 *   missing: [
 *     {
 *       code: "E_LAYER_ONTOLOGY_GAP",
 *       howToFix: "补充 rdfs:label / skos:prefLabel，或收窄问题范围",
 *       layer: "ontology",
 *       nearbyTerms: [
 *         {
 *           label: "供货方",
 *           similarity: 0.67,
 *           term: "urn:coa:party:supplier"
 *         }
 *       ],
 *       span: [
 *         8,
 *         11
 *       ],
 *       text: "供应商",
 *       what: "本体未声明「供应商」"
 *     },
 *     {
 *       candidates: [
 *         {
 *           id: "on_time_delivery_rate",
 *           label: "交货及时率",
 *           score: 0.71
 *         }
 *       ],
 *       code: "E_LAYER_METRICS_GAP",
 *       howToFix: "指定 metricId，或补充指标名称/别名",
 *       layer: "metrics",
 *       what: "未匹配到可求值口径指标"
 *     }
 *   ],
 *   ontologyGraph: "https://coa.local/graph/ed70a15c-2d42-4dc9-8c61-33b2584f05fd/urn%3Acoa%3Aontology%3Av3",
 *   ontologyVersion: "v3",
 *   query: "上个季度供应商交货及时率是多少？",
 *   reasonCode: "E_ANSWER_METRIC_NOT_FOUND",
 *   reasons: [
 *     "facts layer has no metric to evaluate"
 *   ],
 *   termCount: 148,
 *   termSource: "skos(prefLabel/altLabel) when present + rdfs:label baseline",
 *   threshold: 0.8,
 *   timings: {
 *     factsMs: 0,
 *     metricMs: 2,
 *     termsMs: 9
 *   },
 *   valueAnswerable: false
 * }
 * *\/
 * ```
 *
 * @public
 */
export class CheckAnswerableCommand extends $Command
  .classBuilder<
    CheckAnswerableCommandInput,
    CheckAnswerableCommandOutput,
    DataLayerServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: DataLayerServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("DataLayerService", "CheckAnswerable", {})
  .n("DataLayerServiceClient", "CheckAnswerableCommand")
  .sc(CheckAnswerable$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: CheckAnswerableInput;
      output: CheckAnswerableOutput;
    };
    sdk: {
      input: CheckAnswerableCommandInput;
      output: CheckAnswerableCommandOutput;
    };
  };
}
