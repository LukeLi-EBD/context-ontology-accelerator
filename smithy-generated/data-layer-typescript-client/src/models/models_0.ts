// smithy-typescript generated code
import type { DimensionOperator, QueryMode, QueryStrategy, TraversalDirection } from "./enums";

/**
 * A ranked candidate for the question as a whole.
 * @public
 */
export interface AnswerCandidate {
  /**
   * Layer the candidate belongs to.
   * @public
   */
  layer: string | undefined;

  /**
   * Candidate identifier.
   * @public
   */
  id: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label: string | undefined;

  /**
   * Why the candidate matched.
   * @public
   */
  reason: string | undefined;

  /**
   * Match score in 0..1.
   * @public
   */
  score: number | undefined;
}

/**
 * Per-layer evaluation timings.
 * @public
 */
export interface AnswerTimings {
  /**
   * Ontology/term layer duration in milliseconds.
   * @public
   */
  termsMs: number | undefined;

  /**
   * Metric matching duration in milliseconds.
   * @public
   */
  metricMs: number | undefined;

  /**
   * Fact layer duration in milliseconds.
   * @public
   */
  factsMs: number | undefined;
}

/**
 * Input for CheckAnswerable.
 * @public
 */
export interface CheckAnswerableInput {
  /**
   * Namespace the question is asked in.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * The natural-language question to pre-check.
   * @public
   */
  query: string | undefined;

  /**
   * Ontology version to check against; defaults to the published current one.
   * @public
   */
  ontologyVersion?: string | undefined;

  /**
   * Minimum term coverage (0..1) required for `answerable: true`.
   * @public
   */
  minCoverage?: number | undefined;
}

/**
 * Character accounting behind the ontology/term coverage ratio.
 * @public
 */
export interface CoverageChars {
  /**
   * Number of content characters covered by a matched term.
   * @public
   */
  covered: number | undefined;

  /**
   * Number of content characters in the question (stopwords/punctuation removed).
   * @public
   */
  total: number | undefined;
}

/**
 * Layer-specific evidence for one match.
 * @public
 */
export interface LayerMatch {
  /**
   * Matched identifier (term IRI or metric id).
   * @public
   */
  id?: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label?: string | undefined;

  /**
   * Predicate that produced the match (ontology layer).
   * @public
   */
  predicate?: string | undefined;

  /**
   * Source of the label: `rdfs:label` or `skos`.
   * @public
   */
  source?: string | undefined;

  /**
   * Match score (metrics layer).
   * @public
   */
  score?: number | undefined;

  /**
   * Metric this evidence belongs to (facts layer).
   * @public
   */
  metricId?: string | undefined;

  /**
   * Fact coverage status for that metric.
   * @public
   */
  status?: string | undefined;

  /**
   * Stable machine-readable status code.
   * @public
   */
  code?: string | undefined;

  /**
   * Number of fact rows backing the metric.
   * @public
   */
  observationRows?: number | undefined;

  /**
   * Fact function declared by the metric.
   * @public
   */
  factFunction?: string | undefined;
}

/**
 * One of the four answerability layers.
 * @public
 */
export interface CoverageLayer {
  /**
   * Layer name: `ontology` | `terms` | `metrics` | `facts`.
   * @public
   */
  layer: string | undefined;

  /**
   * `covered` | `partial` | `missing` | `degraded` | `unavailable` | `not_applicable`.
   * @public
   */
  status: string | undefined;

  /**
   * Layer coverage in 0..1. Absent when the layer cannot be computed;
   * clients must render that as "unavailable", never as 0.
   * @public
   */
  coverage?: number | undefined;

  /**
   * Evidence that matched in this layer. Fields are layer-specific: ontology
   * and term matches carry id/label/predicate/source, metrics carry
   * id/label/score, facts carry metricId/status/code/observationRows.
   * @public
   */
  matched: LayerMatch[] | undefined;

  /**
   * Short human-readable descriptions of what this layer lacks.
   * @public
   */
  missing: string[] | undefined;
}

/**
 * A term that matched part of the question.
 * @public
 */
export interface MatchedTerm {
  /**
   * Term IRI.
   * @public
   */
  term: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label: string | undefined;

  /**
   * Inclusive-exclusive [start, end) character span in the normalized question.
   * @public
   */
  span: number[] | undefined;
}

/**
 * A ranked candidate that may close a gap.
 * @public
 */
export interface GapCandidate {
  /**
   * Candidate identifier (metric id).
   * @public
   */
  id: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label: string | undefined;

  /**
   * Match score in 0..1.
   * @public
   */
  score: number | undefined;
}

/**
 * A lexically similar term offered for an uncovered fragment.
 * @public
 */
export interface NearbyTerm {
  /**
   * Term IRI.
   * @public
   */
  term: string | undefined;

  /**
   * Human-readable label.
   * @public
   */
  label: string | undefined;

  /**
   * Lexical similarity in 0..1.
   * @public
   */
  similarity: number | undefined;
}

/**
 * A gap: what is missing, in which layer, and how to fix it (F79).
 * @public
 */
export interface MissingGap {
  /**
   * Layer the gap belongs to: `ontology` | `terms` | `metrics` | `facts`.
   * @public
   */
  layer: string | undefined;

  /**
   * Stable machine-readable code, e.g. `E_LAYER_ONTOLOGY_GAP`.
   * @public
   */
  code: string | undefined;

  /**
   * The question fragment that could not be covered (ontology layer).
   * @public
   */
  text?: string | undefined;

  /**
   * Inclusive-exclusive [start, end) span of that fragment, when known.
   * @public
   */
  span?: number[] | undefined;

  /**
   * What exactly is missing, phrased as an operator action target.
   * @public
   */
  what?: string | undefined;

  /**
   * How to close the gap.
   * @public
   */
  howToFix?: string | undefined;

  /**
   * Metric this gap belongs to (facts layer).
   * @public
   */
  metricId?: string | undefined;

  /**
   * Lexically nearby terms that may be the intended concept.
   * @public
   */
  nearbyTerms?: NearbyTerm[] | undefined;

  /**
   * Ranked candidates that may close this gap.
   * @public
   */
  candidates?: GapCandidate[] | undefined;
}

/**
 * Result of an answerability pre-check.
 * @public
 */
export interface CheckAnswerableOutput {
  /**
   * Echo of the checked question.
   * @public
   */
  query: string | undefined;

  /**
   * True when the question can be answered: term coverage meets the
   * threshold, or an exact metric match supports a definition answer even
   * when no fact rows are available.
   * @public
   */
  answerable: boolean | undefined;

  /**
   * True when a concrete numeric value can be produced (facts layer covered).
   * @public
   */
  valueAnswerable: boolean | undefined;

  /**
   * How the question can be answered: `value`, `definition` or `none`.
   * @public
   */
  answerMode: string | undefined;

  /**
   * Detected question intent: `value` or `definition`.
   * @public
   */
  intent: string | undefined;

  /**
   * True when any layer is degraded or unavailable.
   * @public
   */
  degraded: boolean | undefined;

  /**
   * Character coverage of the ontology/term layer (0..1).
   * @public
   */
  coverage: number | undefined;

  /**
   * Threshold used to decide `answerable`.
   * @public
   */
  threshold: number | undefined;

  /**
   * Covered / total content characters behind `coverage`.
   * @public
   */
  coverageChars: CoverageChars | undefined;

  /**
   * Ontology version the check ran against.
   * @public
   */
  ontologyVersion: string | undefined;

  /**
   * Named graph URI of that version.
   * @public
   */
  ontologyGraph: string | undefined;

  /**
   * Human-readable description of the term source used.
   * @public
   */
  termSource: string | undefined;

  /**
   * Number of distinct terms considered.
   * @public
   */
  termCount: number | undefined;

  /**
   * Terms that matched the question.
   * @public
   */
  matchedTerms: MatchedTerm[] | undefined;

  /**
   * Exactly four layers, in order: ontology, terms, metrics, facts.
   * @public
   */
  layers: CoverageLayer[] | undefined;

  /**
   * One entry per gap, each carrying what is missing and how to fix it (F79).
   * @public
   */
  missing: MissingGap[] | undefined;

  /**
   * Ranked candidates that could close the gaps.
   * @public
   */
  candidates: AnswerCandidate[] | undefined;

  /**
   * Machine-readable reasons collected while evaluating.
   * @public
   */
  reasons: string[] | undefined;

  /**
   * Machine-readable reason when `answerable` is false.
   * @public
   */
  reasonCode?: string | undefined;

  /**
   * Operator-facing next step when `answerable` is false.
   * @public
   */
  hint?: string | undefined;

  /**
   * Per-layer evaluation timings in milliseconds.
   * @public
   */
  timings: AnswerTimings | undefined;
}

/**
 * A confidence score in [0, 1] for a query result, with an optional rationale
 * explaining how it was derived.
 * @public
 */
export interface ConfidenceScore {
  /**
   * Confidence score in the range [0, 1].
   * @public
   */
  score: number | undefined;

  /**
   * Explanation of how the score was derived.
   * @public
   */
  rationale?: string | undefined;
}

/**
 * A warning raised when a result row does not conform to the expected SHACL
 * shape, identifying the offending row and shape.
 * @public
 */
export interface ConformanceWarning {
  /**
   * Index of the result row that failed conformance.
   * @public
   */
  row: number | undefined;

  /**
   * Identifier of the SHACL shape that was violated.
   * @public
   */
  shape: string | undefined;

  /**
   * Human-readable description of the conformance warning.
   * @public
   */
  message: string | undefined;
}

/**
 * @public
 */
export interface DescribeSchemaInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Whether to include class properties in the response.
   * @public
   */
  includeProperties?: boolean | undefined;

  /**
   * Maximum number of classes to return.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * A property of a schema class, with its IRI, label, value range (datatype or
 * target class), and optional description.
 * @public
 */
export interface SchemaProperty {
  /**
   * IRI identifying the property.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label for the property.
   * @public
   */
  label: string | undefined;

  /**
   * Value range of the property (datatype or target class).
   * @public
   */
  range?: string | undefined;

  /**
   * Description of the property.
   * @public
   */
  description?: string | undefined;
}

/**
 * A class in the namespace's queryable schema, with its IRI, label, optional
 * description, properties, and parent class.
 * @public
 */
export interface SchemaClass {
  /**
   * IRI identifying the class.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label for the class.
   * @public
   */
  label: string | undefined;

  /**
   * Description of the class.
   * @public
   */
  description?: string | undefined;

  /**
   * Properties defined on the class.
   * @public
   */
  properties?: SchemaProperty[] | undefined;

  /**
   * IRI of the parent class, if any.
   * @public
   */
  parentClass?: string | undefined;
}

/**
 * @public
 */
export interface DescribeSchemaOutput {
  /**
   * The classes in the namespace's schema.
   * @public
   */
  classes: SchemaClass[] | undefined;

  /**
   * Version of the ontology described.
   * @public
   */
  ontologyVersion?: string | undefined;
}

/**
 * @public
 */
export interface GraphTraverseInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * IRI of the entity to start traversal from.
   * @public
   */
  startUri: string | undefined;

  /**
   * Maximum traversal depth from the starting entity. Defaults to 2.
   * Depths above 2 are accepted but currently traverse 2 hops.
   * @public
   */
  maxDepth?: number | undefined;

  /**
   * Accepted and validated, but not yet applied: traversal currently
   * follows every relationship. Reserved for restricting traversal to
   * these relationship (predicate) IRIs.
   * @public
   */
  relationshipFilter?: string[] | undefined;

  /**
   * Accepted and validated, but not yet applied: traversal currently
   * follows relationships in both directions. Defaults to `both`.
   * @public
   */
  direction?: TraversalDirection | undefined;

  /**
   * Maximum number of entities to return. Defaults to 100.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * An entity (graph node) with its IRI, human-readable label, optional type, and
 * arbitrary properties.
 * @public
 */
export interface Entity {
  /**
   * IRI identifying the entity.
   * @public
   */
  uri: string | undefined;

  /**
   * Human-readable label for the entity.
   * @public
   */
  label: string | undefined;

  /**
   * Type (class IRI) of the entity, if known.
   * @public
   */
  type?: string | undefined;

  /**
   * Arbitrary key-value properties of the entity. The reserved
   * `supportingStatements` key contains a JSON-encoded string array of
   * graph-only evidence. Decode that value as JSON before reading it.
   * @public
   */
  properties?: Record<string, string> | undefined;
}

/**
 * A directed relationship between two entities, identified by source, predicate,
 * and target IRIs.
 * @public
 */
export interface Relationship {
  /**
   * IRI of the source entity.
   * @public
   */
  sourceUri: string | undefined;

  /**
   * IRI of the predicate linking source to target. A property-graph edge that
   * carries only a human-readable predicate string is given a stable,
   * tenant-scoped synthetic identifier in the `urn:coa:graph-predicate:` scheme,
   * derived from that string. Treat such a value as an opaque identity for
   * correlating edges within one namespace, not as an ontology predicate IRI.
   * @public
   */
  predicateUri: string | undefined;

  /**
   * IRI of the target entity.
   * @public
   */
  targetUri: string | undefined;

  /**
   * Human-readable label for the predicate.
   * @public
   */
  predicateLabel?: string | undefined;
}

/**
 * One step in a query's execution trace, recording what ran, its status,
 * timing, and any tool used or conformance warnings raised.
 * @public
 */
export interface TraceStep {
  /**
   * Name of the execution step.
   * @public
   */
  step: string | undefined;

  /**
   * Status of the step (e.g. success or failure).
   * @public
   */
  status: string | undefined;

  /**
   * Duration of the step in milliseconds.
   * @public
   */
  durationMs?: number | undefined;

  /**
   * Additional detail about the step.
   * @public
   */
  detail?: string | undefined;

  /**
   * Name of the tool invoked during the step, if any.
   * @public
   */
  toolUsed?: string | undefined;

  /**
   * Identifier of the parallel group this step ran in, if any.
   * @public
   */
  parallelGroup?: string | undefined;

  /**
   * Wall-clock time for the step in milliseconds.
   * @public
   */
  wallMs?: number | undefined;

  /**
   * Conformance warnings raised during the step.
   * @public
   */
  conformanceWarnings?: ConformanceWarning[] | undefined;
}

/**
 * @public
 */
export interface GraphTraverseOutput {
  /**
   * Entities reached during traversal.
   * @public
   */
  entities: Entity[] | undefined;

  /**
   * Relationships traversed.
   * @public
   */
  relationships: Relationship[] | undefined;

  /**
   * Step-by-step trace of the traversal.
   * @public
   */
  trace: TraceStep[] | undefined;
}

/**
 * @public
 */
export interface KBSearchInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Natural-language search query.
   * @public
   */
  query: string | undefined;

  /**
   * Maximum number of chunks to return.
   * @public
   */
  topK?: number | undefined;

  /**
   * Minimum relevance score a chunk must meet to be returned. Relevance
   * scores are non-negative; no upper bound is set because the scale
   * depends on the index's similarity metric.
   * @public
   */
  minScore?: number | undefined;

  /**
   * Not yet supported; a non-empty value is rejected with 400. Reserved
   * for restricting results to these source document identifiers. An
   * empty list is accepted and restricts nothing.
   * @public
   */
  sourceFilter?: string[] | undefined;

  /**
   * Not yet supported; a non-empty value is rejected with 400. Reserved
   * for restricting results to chunks annotated with these entities. An
   * empty list is accepted and restricts nothing.
   * @public
   */
  entityFilter?: string[] | undefined;
}

/**
 * A knowledge-base chunk that supports an answer, with its text, source
 * document provenance, and relevance score.
 * @public
 */
export interface SupportingContent {
  /**
   * Identifier of the knowledge-base chunk.
   * @public
   */
  chunkId: string | undefined;

  /**
   * Text content of the chunk.
   * @public
   */
  text: string | undefined;

  /**
   * Opaque, unique identifier of the source document the chunk came from.
   * Use this value to correlate chunks; it is not a display name.
   * @public
   */
  sourceDocumentId?: string | undefined;

  /**
   * Human-readable original file name of the source document. This value is
   * intended for display and is not guaranteed to be unique.
   * @public
   */
  sourceDocumentName?: string | undefined;

  /**
   * Relevance score of the chunk to the query.
   * @public
   */
  relevanceScore?: number | undefined;

  /**
   * Entities annotated within the chunk.
   * @public
   */
  entityAnnotations?: string[] | undefined;
}

/**
 * @public
 */
export interface KBSearchOutput {
  /**
   * Ranked supporting chunks matching the query.
   * @public
   */
  chunks: SupportingContent[] | undefined;

  /**
   * Step-by-step trace of the search.
   * @public
   */
  trace: TraceStep[] | undefined;

  /**
   * Identifier of the embedding model used for the query.
   * @public
   */
  queryEmbeddingModel?: string | undefined;
}

/**
 * A filter constraining a query to rows matching a dimension value, with an
 * optional comparison operator (defaults to equality).
 *
 * Server-side invariants NOT expressible as Smithy traits, enforced at
 * validation (a violation is a 400, see the Context Manager's InvokeRequest):
 *   - `name` must be non-blank, and is trimmed before use.
 *   - `name` is matched case-insensitively, and must be UNIQUE across the list —
 *     a mapping cannot express two values for one dimension. (`@uniqueItems`
 *     would not capture this: it compares whole structures, so two filters on
 *     the same name with different values would still pass.)
 *   - every filter must be applicable by the resolved metric; a filter the
 *     metric cannot apply fails closed rather than being dropped.
 * @public
 */
export interface DimensionFilter {
  /**
   * Name of the dimension to filter on.
   * @public
   */
  name: string | undefined;

  /**
   * Value to match for the dimension. For compatibility, the server also
   * accepts a JSON number (finite) or boolean here and binds it as a typed
   * literal; `null`, objects, and arrays are rejected.
   * @public
   */
  value: string | undefined;

  /**
   * Comparison operator to apply (defaults to equality). An empty or
   * whitespace-only string is treated as absent.
   * @public
   */
  operator?: DimensionOperator | undefined;
}

/**
 * @public
 */
export interface QueryInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Natural-language question to answer.
   * @public
   */
  query: string | undefined;

  /**
   * Whether to execute the generated query (versus translate only).
   * @public
   */
  execute?: boolean | undefined;

  /**
   * Pin resolution to a specific tier (1, 2 or 3), bypassing automatic routing.
   * @public
   */
  tierOverride?: number | undefined;

  /**
   * Execution mode: "standard" (single-shot) or "deep-reasoning" (multi-step
   * reasoning loop). Orthogonal to the tier cascade. Absent = the serve
   * deployment default. Deep reasoning is higher-recall but much slower
   * (p50 ~90s), so a caller behind a short client timeout should send
   * "standard". "agentic" is the deprecated pre-rename spelling of
   * "deep-reasoning" and is still accepted.
   * @public
   */
  mode?: QueryMode | undefined;

  /**
   * Which Tier-2 engine answers a structured query. Absent = the serve
   * default (``nl_to_sql_first``). Orthogonal to ``mode`` — see
   * ``QueryStrategy``. Ignored when the resolved tier is not 2.
   * @public
   */
  strategy?: QueryStrategy | undefined;

  /**
   * Dimension filters to constrain the query.
   * @public
   */
  dimensions?: DimensionFilter[] | undefined;

  /**
   * Maximum time to wait for the query, in milliseconds. A caller may
   * narrow the service's own REST budget (29,000 ms) but not widen it.
   * @public
   */
  timeoutMs?: number | undefined;

  /**
   * Whether to include supporting content in the response. When false,
   * `supportingContent` and the `supportingStatements` property of each
   * `graphContext` entity are omitted; the entities and relationships are
   * still returned.
   * @public
   */
  includeSupporting?: boolean | undefined;

  /**
   * When true, include the generated SQL (`queryUsed`) and SPARQL
   * (`sparqlGenerated`) in the response for debugging and observability.
   * Defaults to false; when unset or false, both fields are omitted.
   *
   * **Security:** these fields expose internal schema (table and column
   * names, joins), so the flag is honoured only for a caller who already
   * administers that schema: a platform admin, or a namespace owner,
   * maintainer or data steward of the queried namespace. For any other
   * caller the request still succeeds, but both fields are omitted as if
   * the flag were false.
   * @public
   */
  includeDebugInfo?: boolean | undefined;

  /**
   * Maximum number of result rows to return.
   * @public
   */
  maxResults?: number | undefined;
}

/**
 * Graph context accompanying an answer: the entities and relationships that
 * were traversed or cited.
 * @public
 */
export interface GraphContext {
  /**
   * Entities traversed or cited for the answer. Bounded to 200 entities per
   * response; a traversal that reached more is reported through
   * `metadata.degradedSources` and the processing trace.
   * @public
   */
  entities?: Entity[] | undefined;

  /**
   * Relationships traversed or cited for the answer. Bounded to 500
   * relationships per response; a traversal that reached more is reported
   * through `metadata.degradedSources` and the processing trace. A relationship
   * the graph carries without a predicate identifier cannot be represented (see
   * `predicateUri`) and is reported the same way, so an empty list is never
   * ambiguous between "none found" and "all discarded".
   * @public
   */
  relationships?: Relationship[] | undefined;
}

/**
 * The top-level result of a query: the answering tier, confidence, tabular
 * rows and/or a synthesized answer, the query that ran, supporting content,
 * graph context, and an execution trace.
 * @public
 */
export interface QueryResult {
  /**
   * The answering tier that produced this result.
   * @public
   */
  tier: number | undefined;

  /**
   * A confidence score in [0, 1] for a query result, with an optional rationale
   * explaining how it was derived.
   * @public
   */
  confidence: ConfidenceScore | undefined;

  /**
   * Tabular result rows returned by the query.
   * @public
   */
  resultRows?: Record<string, string>[] | undefined;

  /**
   * Natural-language answer synthesized from the results.
   * @public
   */
  synthesizedAnswer?: string | undefined;

  /**
   * The query that was executed to produce the result.
   * @public
   */
  queryUsed?: string | undefined;

  /**
   * The SPARQL query generated for the result, if any.
   * @public
   */
  sparqlGenerated?: string | undefined;

  /**
   * Knowledge-base chunks supporting the answer.
   * @public
   */
  supportingContent?: SupportingContent[] | undefined;

  /**
   * Graph context accompanying an answer: the entities and relationships that
   * were traversed or cited.
   * @public
   */
  graphContext?: GraphContext | undefined;

  /**
   * Step-by-step execution trace of the query.
   * @public
   */
  trace: TraceStep[] | undefined;

  /**
   * Version of the ontology the query ran against.
   * @public
   */
  ontologyVersion?: string | undefined;

  /**
   * Identifiers of the data sources that contributed to the result.
   * @public
   */
  dataSources?: string[] | undefined;

  /**
   * Whether the result is partial (incomplete).
   * @public
   */
  partial?: boolean | undefined;

  /**
   * The execution mode that produced this result: "standard" or
   * "deep-reasoning". Deep Reasoning is a mode orthogonal to the tier
   * cascade, so a client labels an answer by this field rather than
   * inferring mode from `tier` (a Deep Reasoning answer resolves at tier 3
   * but is not Standard mode's Tier-3 result). Absent on responses that do
   * not set it.
   * @public
   */
  executionMode?: string | undefined;
}

/**
 * @public
 */
export interface QueryOutput {
  /**
   * The top-level result of a query: the answering tier, confidence, tabular
   * rows and/or a synthesized answer, the query that ran, supporting content,
   * graph context, and an execution trace.
   * @public
   */
  result: QueryResult | undefined;

  /**
   * Identifier of the request, for tracing and support.
   * @public
   */
  requestId?: string | undefined;

  /**
   * Identifier of the session the request belongs to.
   * @public
   */
  sessionId?: string | undefined;
}

/**
 * The namespace and the statement to run.
 * @public
 */
export interface RunSparqlInput {
  /**
   * The namespace whose graphs the query may read.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * SPARQL text: one SELECT or ASK statement.
   * @public
   */
  sparql: string | undefined;
}

/**
 * One executed statement: its form, the ASK answer, or the SELECT columns and rows.
 * @public
 */
export interface RunSparqlOutput {
  /**
   * The executed form: `SELECT` or `ASK`.
   * @public
   */
  form: string | undefined;

  /**
   * The ASK answer; present only when `form` is `ASK`.
   * @public
   */
  answer?: boolean | undefined;

  /**
   * Column names, in the provider's order (SELECT only).
   * @public
   */
  variables?: string[] | undefined;

  /**
   * Rows, each aligned to `variables` (SELECT only).
   * @public
   */
  rows?: string[][] | undefined;

  /**
   * Rows the provider produced before the 5,000-row display cap (SELECT only).
   * @public
   */
  rowCount: number | undefined;

  /**
   * Rows actually returned in `rows` (SELECT only; at most 5,000).
   * @public
   */
  returnedRows: number | undefined;

  /**
   * True when the provider produced more than 5,000 rows and `rows` was cut.
   * @public
   */
  truncated: boolean | undefined;

  /**
   * Number of namespace graphs the query was confined to.
   * @public
   */
  graphCount: number | undefined;

  /**
   * Server-side execution time in milliseconds.
   * @public
   */
  elapsedMs?: number | undefined;
}

/**
 * @public
 */
export interface TranslateSPARQLInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Natural-language question to translate into SPARQL.
   * @public
   */
  query: string | undefined;
}

/**
 * @public
 */
export interface TranslateSPARQLOutput {
  /**
   * The SPARQL query generated from the question.
   * @public
   */
  sparqlQuery: string | undefined;

  /**
   * A confidence score in [0, 1] for a query result, with an optional rationale
   * explaining how it was derived.
   * @public
   */
  confidence: ConfidenceScore | undefined;

  /**
   * Step-by-step trace of the translation.
   * @public
   */
  trace: TraceStep[] | undefined;

  /**
   * Version of the ontology the query was generated against.
   * @public
   */
  ontologyVersion?: string | undefined;
}

/**
 * @public
 */
export interface DownloadDocumentInput {
  /**
   * UUID v4 identifier.
   * @public
   */
  namespaceId: string | undefined;

  /**
   * Document whose bytes to download.
   * @public
   */
  documentId: string | undefined;
}

/**
 * @public
 */
export interface DownloadDocumentOutput {
  /**
   * Exact stored bytes; empty (0 bytes) when the document was uploaded
   * with empty content.
   * @public
   */
  content?: Uint8Array | undefined;

  /**
   * SHA-256 of `content`, lowercase hex. Equals the `contentHash`
   * returned by `UploadDocument` for the same stored bytes.
   * @public
   */
  contentSha256: string | undefined;
}
