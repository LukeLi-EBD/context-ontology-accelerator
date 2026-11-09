// smithy-typescript generated code
/**
 * @public
 * @enum
 */
export const TraversalDirection = {
  /**
   * Follow relationships in both directions.
   */
  BOTH: "both",
  /**
   * Follow relationships pointing toward the start entity.
   */
  INCOMING: "incoming",
  /**
   * Follow relationships pointing away from the start entity.
   */
  OUTGOING: "outgoing",
} as const;
/**
 * @public
 */
export type TraversalDirection = (typeof TraversalDirection)[keyof typeof TraversalDirection];

/**
 * @public
 * @enum
 */
export const DimensionOperator = {
  /**
   * Match rows whose dimension equals the value.
   */
  EQUALS: "=",
} as const;
/**
 * @public
 */
export type DimensionOperator = (typeof DimensionOperator)[keyof typeof DimensionOperator];

/**
 * @public
 * @enum
 */
export const QueryMode = {
  /**
   * Deprecated pre-rename spelling of `deep-reasoning`; still accepted.
   */
  AGENTIC: "agentic",
  /**
   * Multi-step reasoning loop. Higher recall, much slower (p50 ~90s).
   */
  DEEP_REASONING: "deep-reasoning",
  /**
   * Single-shot retrieval and synthesis.
   */
  STANDARD: "standard",
} as const;
/**
 * @public
 */
export type QueryMode = (typeof QueryMode)[keyof typeof QueryMode];

/**
 * @public
 * @enum
 */
export const QueryStrategy = {
  /**
   * Run Ontop and NL→SQL in parallel; return the higher-confidence answer.
   */
  BEST: "best",
  /**
   * The bounded tool-use agent only. Opt-in; never reached as a fallback.
   */
  DEEP_REASONING: "deep-reasoning",
  /**
   * Native graph strategy only — NL→SPARQL executed directly against the
   * matched RDF_SPARQL source's endpoint (no VKG, no SQL). Auto-selected for
   * namespaces with a graph source; never a fallback for a SQL-only namespace.
   */
  NL_TO_SPARQL: "nl_to_sparql",
  /**
   * NL→SQL only. No Ontop fallback.
   */
  NL_TO_SQL: "nl_to_sql",
  /**
   * NL→SQL first, falling back to Ontop. The serve default.
   */
  NL_TO_SQL_FIRST: "nl_to_sql_first",
  /**
   * Ontop only — the R2RML/VKG semantic path. No NL→SQL fallback.
   */
  ONTOP: "ontop",
  /**
   * Ontop first, falling back to NL→SQL.
   */
  ONTOP_FIRST: "ontop_first",
} as const;
/**
 * @public
 */
export type QueryStrategy = (typeof QueryStrategy)[keyof typeof QueryStrategy];
