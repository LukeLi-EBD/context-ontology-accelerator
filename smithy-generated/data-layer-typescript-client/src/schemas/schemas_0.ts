const _AC = "AnswerCandidate";
const _ACL = "AnswerCandidateList";
const _ADE = "AccessDeniedError";
const _AT = "AnswerTimings";
const _CA = "CheckAnswerable";
const _CAI = "CheckAnswerableInput";
const _CAO = "CheckAnswerableOutput";
const _CC = "CoverageChars";
const _CD = "CustomerData";
const _CL = "CoverageLayer";
const _CLL = "CoverageLayerList";
const _CS = "ConfidenceScore";
const _CW = "ConformanceWarning";
const _CWL = "ConformanceWarningList";
const _DD = "DownloadDocument";
const _DDI = "DownloadDocumentInput";
const _DDO = "DownloadDocumentOutput";
const _DF = "DimensionFilter";
const _DFL = "DimensionFilterList";
const _DS = "DescribeSchema";
const _DSI = "DescribeSchemaInput";
const _DSO = "DescribeSchemaOutput";
const _DSUE = "DataSourceUnavailableError";
const _E = "Entity";
const _EL = "EntityList";
const _EM = "EntityMention";
const _EML = "EntityMentionList";
const _GC = "GapCandidate";
const _GCL = "GapCandidateList";
const _GCr = "GraphContext";
const _GT = "GraphTraverse";
const _GTI = "GraphTraverseInput";
const _GTO = "GraphTraverseOutput";
const _ISE = "InternalServerError";
const _KBS = "KBSearch";
const _KBSI = "KBSearchInput";
const _KBSO = "KBSearchOutput";
const _LM = "LayerMatch";
const _LML = "LayerMatchList";
const _MG = "MissingGap";
const _MGL = "MissingGapList";
const _MT = "MatchedTerm";
const _MTL = "MatchedTermList";
const _NFE = "NotFoundError";
const _NLQ = "NaturalLanguageQuery";
const _NNFE = "NamespaceNotFoundError";
const _NRE = "NoResultError";
const _NT = "NearbyTerm";
const _NTL = "NearbyTermList";
const _ONPE = "OntologyNotPublishedError";
const _Q = "Query";
const _QI = "QueryInput";
const _QO = "QueryOutput";
const _QR = "QueryResult";
const _QTE = "QueryTranslationError";
const _R = "Relationship";
const _RL = "RelationshipList";
const _RLEE = "RateLimitExceededError";
const _RR = "ResultRow";
const _RRL = "ResultRowList";
const _RS = "RunSparql";
const _RSI = "RunSparqlInput";
const _RSO = "RunSparqlOutput";
const _SBRE = "SparqlBadRequestError";
const _SC = "SchemaClass";
const _SCL = "SchemaClassList";
const _SCLu = "SupportingContentList";
const _SCu = "SupportingContent";
const _SP = "SchemaProperty";
const _SPE = "SparqlProviderError";
const _SPL = "SchemaPropertyList";
const _SQEE = "SparqlQuotaExceededError";
const _SRL = "SparqlRowList";
const _SRTLE = "SparqlResultTooLargeError";
const _SSTLE = "SparqlScopeTooLargeError";
const _STE = "SparqlTimeoutError";
const _SUE = "ServiceUnavailableError";
const _TS = "TraceStep";
const _TSL = "TraceStepList";
const _TSPARQL = "TranslateSPARQL";
const _TSPARQLI = "TranslateSPARQLInput";
const _TSPARQLO = "TranslateSPARQLOutput";
const _VE = "ValidationError";
const _VKGEE = "VKGExecutionError";
const _XCS = "X-Content-Sha256";
const _a = "answerable";
const _aM = "answerMode";
const _an = "answer";
const _c = "client";
const _cC = "coverageChars";
const _cI = "chunkId";
const _cS = "contentSha256";
const _cW = "conformanceWarnings";
const _ca = "candidates";
const _ch = "chunks";
const _cl = "classes";
const _co = "code";
const _con = "confidence";
const _cont = "content";
const _cov = "coverage";
const _cove = "covered";
const _d = "degraded";
const _dI = "documentId";
const _dM = "durationMs";
const _dS = "dataSources";
const _dSI = "dataSourceId";
const _de = "description";
const _det = "detail";
const _di = "direction";
const _dim = "dimensions";
const _e = "error";
const _eA = "entityAnnotations";
const _eC = "entityCoverage";
const _eCn = "entityCount";
const _eD = "entityDegraded";
const _eDR = "entityDegradeReason";
const _eF = "entityFilter";
const _eM = "entityMentions";
const _eMl = "elapsedMs";
const _eMx = "executionMode";
const _en = "entities";
const _ex = "execute";
const _f = "form";
const _fF = "factFunction";
const _fM = "factsMs";
const _gC = "graphContext";
const _gCr = "graphCount";
const _h = "hint";
const _hE = "httpError";
const _hH = "httpHeader";
const _hQ = "httpQuery";
const _hTF = "howToFix";
const _ht = "http";
const _i = "id";
const _iDI = "includeDebugInfo";
const _iP = "includeProperties";
const _iS = "includeSupporting";
const _in = "intent";
const _k = "kind";
const _l = "layer";
const _la = "label";
const _lay = "layers";
const _m = "message";
const _mC = "minCoverage";
const _mD = "maxDepth";
const _mEC = "matchedEntityCount";
const _mI = "metricId";
const _mM = "metricMs";
const _mR = "maxResults";
const _mS = "minScore";
const _mT = "matchedTerms";
const _ma = "matched";
const _mi = "missing";
const _mo = "mode";
const _n = "name";
const _nI = "namespaceId";
const _nT = "nearbyTerms";
const _o = "operator";
const _oG = "ontologyGraph";
const _oR = "observationRows";
const _oV = "ontologyVersion";
const _p = "properties";
const _pC = "providerCode";
const _pCa = "parentClass";
const _pG = "parallelGroup";
const _pL = "predicateLabel";
const _pM = "providerMessage";
const _pU = "predicateUri";
const _pa = "partial";
const _pr = "predicate";
const _q = "query";
const _qEM = "queryEmbeddingModel";
const _qU = "queryUsed";
const _r = "reason";
const _rAS = "retryAfterSeconds";
const _rC = "reasonCode";
const _rCo = "rowCount";
const _rF = "relationshipFilter";
const _rI = "requestId";
const _rR = "resultRows";
const _rRe = "returnedRows";
const _rS = "relevanceScore";
const _ra = "rationale";
const _ran = "range";
const _re = "reasons";
const _rel = "relationships";
const _res = "result";
const _ro = "row";
const _row = "rows";
const _s = "smithy.ts.sdk.synthetic.com.amazon.semanticcontext.datalayer";
const _sA = "synthesizedAnswer";
const _sC = "supportingContent";
const _sDI = "sourceDocumentId";
const _sDN = "sourceDocumentName";
const _sF = "sourceFilter";
const _sG = "sparqlGenerated";
const _sI = "sessionId";
const _sQ = "sparqlQuery";
const _sU = "startUri";
const _sUo = "sourceUri";
const _sc = "score";
const _se = "server";
const _sh = "shape";
const _si = "similarity";
const _so = "source";
const _sp = "span";
const _spa = "sparql";
const _st = "status";
const _ste = "step";
const _str = "strategy";
const _t = "tier";
const _tC = "termCount";
const _tK = "topK";
const _tM = "termsMs";
const _tMi = "timeoutMs";
const _tO = "tierOverride";
const _tS = "termSource";
const _tU = "targetUri";
const _tUo = "toolUsed";
const _te = "text";
const _ter = "term";
const _th = "threshold";
const _ti = "timings";
const _to = "total";
const _tr = "trace";
const _tru = "truncated";
const _ty = "type";
const _u = "uri";
const _v = "value";
const _vA = "valueAnswerable";
const _va = "variables";
const _w = "what";
const _wM = "wallMs";
const n0 = "com.amazon.semanticcontext.common";
const n1 = "com.amazon.semanticcontext.datalayer";
const n2 = "com.amazon.semanticcontext.documents";

// smithy-typescript generated code
import { TypeRegistry } from "@smithy/core/schema";
import type {
  StaticErrorSchema,
  StaticListSchema,
  StaticMapSchema,
  StaticOperationSchema,
  StaticSimpleSchema,
  StaticStructureSchema,
} from "@smithy/types";

import { DataLayerServiceServiceException } from "../models/DataLayerServiceServiceException";
import {
  AccessDeniedError,
  DataSourceUnavailableError,
  InternalServerError,
  NamespaceNotFoundError,
  NoResultError,
  NotFoundError,
  OntologyNotPublishedError,
  QueryTranslationError,
  RateLimitExceededError,
  ServiceUnavailableError,
  SparqlBadRequestError,
  SparqlProviderError,
  SparqlQuotaExceededError,
  SparqlResultTooLargeError,
  SparqlScopeTooLargeError,
  SparqlTimeoutError,
  ValidationError,
  VKGExecutionError,
} from "../models/errors";

/* eslint no-var: 0 */
const _s_registry = TypeRegistry.for(_s);
export var DataLayerServiceServiceException$: StaticErrorSchema = [-3, _s, "DataLayerServiceServiceException", 0, [], []];
_s_registry.registerError(DataLayerServiceServiceException$, DataLayerServiceServiceException);
const n0_registry = TypeRegistry.for(n0);
const n1_registry = TypeRegistry.for(n1);
export var AccessDeniedError$: StaticErrorSchema = [-3, n0, _ADE,
  { [_e]: _c, [_hE]: 403 },
  [_m],
  [0], 1
];
n0_registry.registerError(AccessDeniedError$, AccessDeniedError);
export var InternalServerError$: StaticErrorSchema = [-3, n0, _ISE,
  { [_e]: _se, [_hE]: 500 },
  [_m],
  [0], 1
];
n0_registry.registerError(InternalServerError$, InternalServerError);
export var NotFoundError$: StaticErrorSchema = [-3, n0, _NFE,
  { [_e]: _c, [_hE]: 404 },
  [_m],
  [0], 1
];
n0_registry.registerError(NotFoundError$, NotFoundError);
export var ServiceUnavailableError$: StaticErrorSchema = [-3, n0, _SUE,
  { [_e]: _se, [_hE]: 503 },
  [_m],
  [0], 1
];
n0_registry.registerError(ServiceUnavailableError$, ServiceUnavailableError);
export var ValidationError$: StaticErrorSchema = [-3, n0, _VE,
  { [_e]: _c },
  [_m],
  [0], 1
];
n0_registry.registerError(ValidationError$, ValidationError);
export var DataSourceUnavailableError$: StaticErrorSchema = [-3, n1, _DSUE,
  { [_e]: _se, [_hE]: 502 },
  [_m, _dSI],
  [0, 0], 1
];
n1_registry.registerError(DataSourceUnavailableError$, DataSourceUnavailableError);
export var NamespaceNotFoundError$: StaticErrorSchema = [-3, n1, _NNFE,
  { [_e]: _c, [_hE]: 404 },
  [_m, _nI],
  [0, 0], 1
];
n1_registry.registerError(NamespaceNotFoundError$, NamespaceNotFoundError);
export var NoResultError$: StaticErrorSchema = [-3, n1, _NRE,
  { [_e]: _c, [_hE]: 404 },
  [_m, _t],
  [0, 1], 1
];
n1_registry.registerError(NoResultError$, NoResultError);
export var OntologyNotPublishedError$: StaticErrorSchema = [-3, n1, _ONPE,
  { [_e]: _c, [_hE]: 409 },
  [_m, _nI],
  [0, 0], 1
];
n1_registry.registerError(OntologyNotPublishedError$, OntologyNotPublishedError);
export var QueryTranslationError$: StaticErrorSchema = [-3, n1, _QTE,
  { [_e]: _c, [_hE]: 400 },
  [_m],
  [0], 1
];
n1_registry.registerError(QueryTranslationError$, QueryTranslationError);
export var RateLimitExceededError$: StaticErrorSchema = [-3, n1, _RLEE,
  { [_e]: _c, [_hE]: 429 },
  [_m, _rAS],
  [0, 1], 1
];
n1_registry.registerError(RateLimitExceededError$, RateLimitExceededError);
export var SparqlBadRequestError$: StaticErrorSchema = [-3, n1, _SBRE,
  { [_e]: _c, [_hE]: 400 },
  [_m, _co, _pC, _pM],
  [0, 0, 0, 0], 2
];
n1_registry.registerError(SparqlBadRequestError$, SparqlBadRequestError);
export var SparqlProviderError$: StaticErrorSchema = [-3, n1, _SPE,
  { [_e]: _se, [_hE]: 502 },
  [_m, _co, _pC, _pM],
  [0, 0, 0, 0], 2
];
n1_registry.registerError(SparqlProviderError$, SparqlProviderError);
export var SparqlQuotaExceededError$: StaticErrorSchema = [-3, n1, _SQEE,
  { [_e]: _c, [_hE]: 429 },
  [_m, _co],
  [0, 0], 2
];
n1_registry.registerError(SparqlQuotaExceededError$, SparqlQuotaExceededError);
export var SparqlResultTooLargeError$: StaticErrorSchema = [-3, n1, _SRTLE,
  { [_e]: _c, [_hE]: 413 },
  [_m, _co],
  [0, 0], 2
];
n1_registry.registerError(SparqlResultTooLargeError$, SparqlResultTooLargeError);
export var SparqlScopeTooLargeError$: StaticErrorSchema = [-3, n1, _SSTLE,
  { [_e]: _se, [_hE]: 503 },
  [_m, _co],
  [0, 0], 2
];
n1_registry.registerError(SparqlScopeTooLargeError$, SparqlScopeTooLargeError);
export var SparqlTimeoutError$: StaticErrorSchema = [-3, n1, _STE,
  { [_e]: _se, [_hE]: 504 },
  [_m, _co],
  [0, 0], 2
];
n1_registry.registerError(SparqlTimeoutError$, SparqlTimeoutError);
export var VKGExecutionError$: StaticErrorSchema = [-3, n1, _VKGEE,
  { [_e]: _se, [_hE]: 502 },
  [_m],
  [0], 1
];
n1_registry.registerError(VKGExecutionError$, VKGExecutionError);
/**
 * TypeRegistry instances containing modeled errors.
 * @internal
 *
 */
export const errorTypeRegistries = [
  _s_registry,
  n0_registry,
  n1_registry,
]
var CustomerData: StaticSimpleSchema = [0, n1, _CD, 8, 0];
var NaturalLanguageQuery: StaticSimpleSchema = [0, n1, _NLQ, 8, 0];
export var AnswerCandidate$: StaticStructureSchema = [3, n1, _AC,
  0,
  [_l, _i, _la, _r, _sc],
  [0, 0, 0, 0, 1], 5
];
export var AnswerTimings$: StaticStructureSchema = [3, n1, _AT,
  0,
  [_tM, _mM, _fM],
  [1, 1, 1], 3
];
export var CheckAnswerableInput$: StaticStructureSchema = [3, n1, _CAI,
  0,
  [_nI, _q, _oV, _mC],
  [[0, 1], 0, 0, 1], 2
];
export var CheckAnswerableOutput$: StaticStructureSchema = [3, n1, _CAO,
  0,
  [_q, _a, _vA, _aM, _in, _d, _cov, _th, _cC, _oV, _oG, _tS, _tC, _mT, _lay, _mi, _ca, _re, _ti, _eC, _eCn, _mEC, _eM, _eD, _eDR, _rC, _h],
  [0, 2, 2, 0, 0, 2, 1, 1, () => CoverageChars$, 0, 0, 0, 1, () => MatchedTermList, () => CoverageLayerList, () => MissingGapList, () => AnswerCandidateList, 64 | 0, () => AnswerTimings$, 1, 1, 1, () => EntityMentionList, 2, 0, 0, 0], 19
];
export var ConfidenceScore$: StaticStructureSchema = [3, n1, _CS,
  0,
  [_sc, _ra],
  [1, 0], 1
];
export var ConformanceWarning$: StaticStructureSchema = [3, n1, _CW,
  0,
  [_ro, _sh, _m],
  [1, 0, 0], 3
];
export var CoverageChars$: StaticStructureSchema = [3, n1, _CC,
  0,
  [_cove, _to],
  [1, 1], 2
];
export var CoverageLayer$: StaticStructureSchema = [3, n1, _CL,
  0,
  [_l, _st, _ma, _mi, _cov],
  [0, 0, () => LayerMatchList, 64 | 0, 1], 4
];
export var DescribeSchemaInput$: StaticStructureSchema = [3, n1, _DSI,
  0,
  [_nI, _iP, _mR],
  [[0, 1], [2, { [_hQ]: _iP }], [1, { [_hQ]: _mR }]], 1
];
export var DescribeSchemaOutput$: StaticStructureSchema = [3, n1, _DSO,
  0,
  [_cl, _oV],
  [() => SchemaClassList, 0], 1
];
export var DimensionFilter$: StaticStructureSchema = [3, n1, _DF,
  0,
  [_n, _v, _o],
  [0, [() => CustomerData, 0], 0], 2
];
export var Entity$: StaticStructureSchema = [3, n1, _E,
  0,
  [_u, _la, _ty, _p],
  [0, 0, 0, 128 | 0], 2
];
export var EntityMention$: StaticStructureSchema = [3, n1, _EM,
  0,
  [_te, _sp, _k, _ter, _la, _so],
  [0, 64 | 1, 0, 0, 0, 0], 3
];
export var GapCandidate$: StaticStructureSchema = [3, n1, _GC,
  0,
  [_i, _la, _sc],
  [0, 0, 1], 3
];
export var GraphContext$: StaticStructureSchema = [3, n1, _GCr,
  0,
  [_en, _rel],
  [() => EntityList, () => RelationshipList]
];
export var GraphTraverseInput$: StaticStructureSchema = [3, n1, _GTI,
  0,
  [_nI, _sU, _mD, _rF, _di, _mR],
  [[0, 1], 0, 1, 64 | 0, 0, 1], 2
];
export var GraphTraverseOutput$: StaticStructureSchema = [3, n1, _GTO,
  0,
  [_en, _rel, _tr],
  [() => EntityList, () => RelationshipList, () => TraceStepList], 3
];
export var KBSearchInput$: StaticStructureSchema = [3, n1, _KBSI,
  0,
  [_nI, _q, _tK, _mS, _sF, _eF],
  [[0, 1], [() => NaturalLanguageQuery, 0], 1, 1, 64 | 0, 64 | 0], 2
];
export var KBSearchOutput$: StaticStructureSchema = [3, n1, _KBSO,
  0,
  [_ch, _tr, _qEM],
  [[() => SupportingContentList, 0], () => TraceStepList, 0], 2
];
export var LayerMatch$: StaticStructureSchema = [3, n1, _LM,
  0,
  [_i, _la, _pr, _so, _sc, _mI, _st, _co, _oR, _fF],
  [0, 0, 0, 0, 1, 0, 0, 0, 1, 0]
];
export var MatchedTerm$: StaticStructureSchema = [3, n1, _MT,
  0,
  [_ter, _la, _sp],
  [0, 0, 64 | 1], 3
];
export var MissingGap$: StaticStructureSchema = [3, n1, _MG,
  0,
  [_l, _co, _te, _sp, _w, _hTF, _mI, _nT, _ca],
  [0, 0, 0, 64 | 1, 0, 0, 0, () => NearbyTermList, () => GapCandidateList], 2
];
export var NearbyTerm$: StaticStructureSchema = [3, n1, _NT,
  0,
  [_ter, _la, _si],
  [0, 0, 1], 3
];
export var QueryInput$: StaticStructureSchema = [3, n1, _QI,
  0,
  [_nI, _q, _ex, _tO, _mo, _str, _dim, _tMi, _iS, _iDI, _mR],
  [[0, 1], [() => NaturalLanguageQuery, 0], 2, 1, 0, 0, [() => DimensionFilterList, 0], 1, 2, 2, 1], 2
];
export var QueryOutput$: StaticStructureSchema = [3, n1, _QO,
  0,
  [_res, _rI, _sI],
  [[() => QueryResult$, 0], 0, 0], 1
];
export var QueryResult$: StaticStructureSchema = [3, n1, _QR,
  0,
  [_t, _con, _tr, _rR, _sA, _qU, _sG, _sC, _gC, _oV, _dS, _pa, _eMx],
  [1, () => ConfidenceScore$, () => TraceStepList, [() => ResultRowList, 0], [() => CustomerData, 0], [() => CustomerData, 0], [() => CustomerData, 0], [() => SupportingContentList, 0], () => GraphContext$, 0, 64 | 0, 2, 0], 3
];
export var Relationship$: StaticStructureSchema = [3, n1, _R,
  0,
  [_sUo, _pU, _tU, _pL],
  [0, 0, 0, 0], 3
];
export var RunSparqlInput$: StaticStructureSchema = [3, n1, _RSI,
  0,
  [_nI, _spa],
  [[0, 1], 0], 2
];
export var RunSparqlOutput$: StaticStructureSchema = [3, n1, _RSO,
  0,
  [_f, _rCo, _rRe, _tru, _gCr, _an, _va, _row, _eMl],
  [0, 1, 1, 2, 1, 2, 64 | 0, [1, n1, _SRL, 0, 64 | 0], 1], 5
];
export var SchemaClass$: StaticStructureSchema = [3, n1, _SC,
  0,
  [_u, _la, _de, _p, _pCa],
  [0, 0, 0, () => SchemaPropertyList, 0], 2
];
export var SchemaProperty$: StaticStructureSchema = [3, n1, _SP,
  0,
  [_u, _la, _ran, _de],
  [0, 0, 0, 0], 2
];
export var SupportingContent$: StaticStructureSchema = [3, n1, _SCu,
  0,
  [_cI, _te, _sDI, _sDN, _rS, _eA],
  [0, [() => CustomerData, 0], 0, 0, 1, 64 | 0], 2
];
export var TraceStep$: StaticStructureSchema = [3, n1, _TS,
  0,
  [_ste, _st, _dM, _det, _tUo, _pG, _wM, _cW],
  [0, 0, 1, 0, 0, 0, 1, () => ConformanceWarningList], 2
];
export var TranslateSPARQLInput$: StaticStructureSchema = [3, n1, _TSPARQLI,
  0,
  [_nI, _q],
  [[0, 1], [() => NaturalLanguageQuery, 0]], 2
];
export var TranslateSPARQLOutput$: StaticStructureSchema = [3, n1, _TSPARQLO,
  0,
  [_sQ, _con, _tr, _oV],
  [0, () => ConfidenceScore$, () => TraceStepList, 0], 3
];
export var DownloadDocumentInput$: StaticStructureSchema = [3, n2, _DDI,
  0,
  [_nI, _dI],
  [[0, 1], [0, 1]], 2
];
export var DownloadDocumentOutput$: StaticStructureSchema = [3, n2, _DDO,
  0,
  [_cS, _cont],
  [[0, { [_hH]: _XCS }], [21, 16]], 1
];
var StringList = 64 | 0;
var AnswerCandidateList: StaticListSchema = [1, n1, _ACL,
  0, () => AnswerCandidate$
];
var ConformanceWarningList: StaticListSchema = [1, n1, _CWL,
  0, () => ConformanceWarning$
];
var CoverageLayerList: StaticListSchema = [1, n1, _CLL,
  0, () => CoverageLayer$
];
var DimensionFilterList: StaticListSchema = [1, n1, _DFL,
  0, [() => DimensionFilter$,
    0]
];
var EntityList: StaticListSchema = [1, n1, _EL,
  0, () => Entity$
];
var EntityMentionList: StaticListSchema = [1, n1, _EML,
  0, () => EntityMention$
];
var FilterValueList = 64 | 0;
var GapCandidateList: StaticListSchema = [1, n1, _GCL,
  0, () => GapCandidate$
];
var LayerMatchList: StaticListSchema = [1, n1, _LML,
  0, () => LayerMatch$
];
var MatchedTermList: StaticListSchema = [1, n1, _MTL,
  0, () => MatchedTerm$
];
var MissingGapList: StaticListSchema = [1, n1, _MGL,
  0, () => MissingGap$
];
var NearbyTermList: StaticListSchema = [1, n1, _NTL,
  0, () => NearbyTerm$
];
var RelationshipList: StaticListSchema = [1, n1, _RL,
  0, () => Relationship$
];
var ResultRowList: StaticListSchema = [1, n1, _RRL,
  0, [() => ResultRow,
    0]
];
var SchemaClassList: StaticListSchema = [1, n1, _SCL,
  0, () => SchemaClass$
];
var SchemaPropertyList: StaticListSchema = [1, n1, _SPL,
  0, () => SchemaProperty$
];
var Span = 64 | 1;
var SparqlRow = 64 | 0;
var SparqlRowList: StaticListSchema = [1, n1, _SRL,
  0, 64 | 0
];
var SparqlVariableList = 64 | 0;
var SupportingContentList: StaticListSchema = [1, n1, _SCLu,
  0, [() => SupportingContent$,
    0]
];
var TraceStepList: StaticListSchema = [1, n1, _TSL,
  0, () => TraceStep$
];
var PropertyMap = 128 | 0;
var ResultRow: StaticMapSchema = [2, n1, _RR,
  0, [0,
    0]
  , [() => CustomerData,
    0]
];
export var CheckAnswerable$: StaticOperationSchema = [9, n1, _CA,
  { [_ht]: ["POST", "/namespaces/{namespaceId}/answerable", 200] }, () => CheckAnswerableInput$, () => CheckAnswerableOutput$
];
export var DescribeSchema$: StaticOperationSchema = [9, n1, _DS,
  { [_ht]: ["GET", "/namespaces/{namespaceId}/schema", 200] }, () => DescribeSchemaInput$, () => DescribeSchemaOutput$
];
export var GraphTraverse$: StaticOperationSchema = [9, n1, _GT,
  { [_ht]: ["POST", "/namespaces/{namespaceId}/graph/traverse", 200] }, () => GraphTraverseInput$, () => GraphTraverseOutput$
];
export var KBSearch$: StaticOperationSchema = [9, n1, _KBS,
  { [_ht]: ["POST", "/namespaces/{namespaceId}/kb/search", 200] }, () => KBSearchInput$, () => KBSearchOutput$
];
export var Query$: StaticOperationSchema = [9, n1, _Q,
  { [_ht]: ["POST", "/namespaces/{namespaceId}/query", 200] }, () => QueryInput$, () => QueryOutput$
];
export var RunSparql$: StaticOperationSchema = [9, n1, _RS,
  { [_ht]: ["POST", "/namespaces/{namespaceId}/sparql", 200] }, () => RunSparqlInput$, () => RunSparqlOutput$
];
export var TranslateSPARQL$: StaticOperationSchema = [9, n1, _TSPARQL,
  { [_ht]: ["POST", "/namespaces/{namespaceId}/translate", 200] }, () => TranslateSPARQLInput$, () => TranslateSPARQLOutput$
];
export var DownloadDocument$: StaticOperationSchema = [9, n2, _DD,
  { [_ht]: ["GET", "/namespaces/{namespaceId}/documents/{documentId}/content", 200] }, () => DownloadDocumentInput$, () => DownloadDocumentOutput$
];
