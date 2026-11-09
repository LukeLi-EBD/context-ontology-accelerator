const _ADE = "AccessDeniedError";
const _CD = "CustomerData";
const _CS = "ConfidenceScore";
const _CW = "ConformanceWarning";
const _CWL = "ConformanceWarningList";
const _DF = "DimensionFilter";
const _DFL = "DimensionFilterList";
const _DS = "DescribeSchema";
const _DSI = "DescribeSchemaInput";
const _DSO = "DescribeSchemaOutput";
const _DSUE = "DataSourceUnavailableError";
const _E = "Entity";
const _EL = "EntityList";
const _GC = "GraphContext";
const _GT = "GraphTraverse";
const _GTI = "GraphTraverseInput";
const _GTO = "GraphTraverseOutput";
const _ISE = "InternalServerError";
const _KBS = "KBSearch";
const _KBSI = "KBSearchInput";
const _KBSO = "KBSearchOutput";
const _NLQ = "NaturalLanguageQuery";
const _NNFE = "NamespaceNotFoundError";
const _NRE = "NoResultError";
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
const _SC = "SchemaClass";
const _SCL = "SchemaClassList";
const _SCLu = "SupportingContentList";
const _SCu = "SupportingContent";
const _SP = "SchemaProperty";
const _SPL = "SchemaPropertyList";
const _SUE = "ServiceUnavailableError";
const _TS = "TraceStep";
const _TSL = "TraceStepList";
const _TSPARQL = "TranslateSPARQL";
const _TSPARQLI = "TranslateSPARQLInput";
const _TSPARQLO = "TranslateSPARQLOutput";
const _VE = "ValidationError";
const _VKGEE = "VKGExecutionError";
const _c = "client";
const _cI = "chunkId";
const _cW = "conformanceWarnings";
const _ch = "chunks";
const _cl = "classes";
const _co = "confidence";
const _d = "direction";
const _dM = "durationMs";
const _dS = "dataSources";
const _dSI = "dataSourceId";
const _de = "description";
const _det = "detail";
const _di = "dimensions";
const _e = "error";
const _eA = "entityAnnotations";
const _eF = "entityFilter";
const _eM = "executionMode";
const _en = "entities";
const _ex = "execute";
const _gC = "graphContext";
const _h = "http";
const _hE = "httpError";
const _hQ = "httpQuery";
const _iDI = "includeDebugInfo";
const _iP = "includeProperties";
const _iS = "includeSupporting";
const _l = "label";
const _m = "message";
const _mD = "maxDepth";
const _mR = "maxResults";
const _mS = "minScore";
const _mo = "mode";
const _n = "name";
const _nI = "namespaceId";
const _o = "operator";
const _oV = "ontologyVersion";
const _p = "properties";
const _pC = "parentClass";
const _pG = "parallelGroup";
const _pL = "predicateLabel";
const _pU = "predicateUri";
const _pa = "partial";
const _q = "query";
const _qEM = "queryEmbeddingModel";
const _qU = "queryUsed";
const _r = "rationale";
const _rAS = "retryAfterSeconds";
const _rF = "relationshipFilter";
const _rI = "requestId";
const _rR = "resultRows";
const _rS = "relevanceScore";
const _ra = "range";
const _re = "relationships";
const _res = "result";
const _ro = "row";
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
const _st = "strategy";
const _sta = "status";
const _ste = "step";
const _t = "tier";
const _tK = "topK";
const _tM = "timeoutMs";
const _tO = "tierOverride";
const _tU = "targetUri";
const _tUo = "toolUsed";
const _te = "text";
const _tr = "trace";
const _ty = "type";
const _u = "uri";
const _v = "value";
const _wM = "wallMs";
const n0 = "com.amazon.semanticcontext.common";
const n1 = "com.amazon.semanticcontext.datalayer";

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
  OntologyNotPublishedError,
  QueryTranslationError,
  RateLimitExceededError,
  ServiceUnavailableError,
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
export var ConfidenceScore$: StaticStructureSchema = [3, n1, _CS,
  0,
  [_sc, _r],
  [1, 0], 1
];
export var ConformanceWarning$: StaticStructureSchema = [3, n1, _CW,
  0,
  [_ro, _sh, _m],
  [1, 0, 0], 3
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
  [_u, _l, _ty, _p],
  [0, 0, 0, 128 | 0], 2
];
export var GraphContext$: StaticStructureSchema = [3, n1, _GC,
  0,
  [_en, _re],
  [() => EntityList, () => RelationshipList]
];
export var GraphTraverseInput$: StaticStructureSchema = [3, n1, _GTI,
  0,
  [_nI, _sU, _mD, _rF, _d, _mR],
  [[0, 1], 0, 1, 64 | 0, 0, 1], 2
];
export var GraphTraverseOutput$: StaticStructureSchema = [3, n1, _GTO,
  0,
  [_en, _re, _tr],
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
export var QueryInput$: StaticStructureSchema = [3, n1, _QI,
  0,
  [_nI, _q, _ex, _tO, _mo, _st, _di, _tM, _iS, _iDI, _mR],
  [[0, 1], [() => NaturalLanguageQuery, 0], 2, 1, 0, 0, [() => DimensionFilterList, 0], 1, 2, 2, 1], 2
];
export var QueryOutput$: StaticStructureSchema = [3, n1, _QO,
  0,
  [_res, _rI, _sI],
  [[() => QueryResult$, 0], 0, 0], 1
];
export var QueryResult$: StaticStructureSchema = [3, n1, _QR,
  0,
  [_t, _co, _tr, _rR, _sA, _qU, _sG, _sC, _gC, _oV, _dS, _pa, _eM],
  [1, () => ConfidenceScore$, () => TraceStepList, [() => ResultRowList, 0], [() => CustomerData, 0], [() => CustomerData, 0], [() => CustomerData, 0], [() => SupportingContentList, 0], () => GraphContext$, 0, 64 | 0, 2, 0], 3
];
export var Relationship$: StaticStructureSchema = [3, n1, _R,
  0,
  [_sUo, _pU, _tU, _pL],
  [0, 0, 0, 0], 3
];
export var SchemaClass$: StaticStructureSchema = [3, n1, _SC,
  0,
  [_u, _l, _de, _p, _pC],
  [0, 0, 0, () => SchemaPropertyList, 0], 2
];
export var SchemaProperty$: StaticStructureSchema = [3, n1, _SP,
  0,
  [_u, _l, _ra, _de],
  [0, 0, 0, 0], 2
];
export var SupportingContent$: StaticStructureSchema = [3, n1, _SCu,
  0,
  [_cI, _te, _sDI, _sDN, _rS, _eA],
  [0, [() => CustomerData, 0], 0, 0, 1, 64 | 0], 2
];
export var TraceStep$: StaticStructureSchema = [3, n1, _TS,
  0,
  [_ste, _sta, _dM, _det, _tUo, _pG, _wM, _cW],
  [0, 0, 1, 0, 0, 0, 1, () => ConformanceWarningList], 2
];
export var TranslateSPARQLInput$: StaticStructureSchema = [3, n1, _TSPARQLI,
  0,
  [_nI, _q],
  [[0, 1], [() => NaturalLanguageQuery, 0]], 2
];
export var TranslateSPARQLOutput$: StaticStructureSchema = [3, n1, _TSPARQLO,
  0,
  [_sQ, _co, _tr, _oV],
  [0, () => ConfidenceScore$, () => TraceStepList, 0], 3
];
var ConformanceWarningList: StaticListSchema = [1, n1, _CWL,
  0, () => ConformanceWarning$
];
var DimensionFilterList: StaticListSchema = [1, n1, _DFL,
  0, [() => DimensionFilter$,
    0]
];
var EntityList: StaticListSchema = [1, n1, _EL,
  0, () => Entity$
];
var FilterValueList = 64 | 0;
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
var StringList = 64 | 0;
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
export var DescribeSchema$: StaticOperationSchema = [9, n1, _DS,
  { [_h]: ["GET", "/namespaces/{namespaceId}/schema", 200] }, () => DescribeSchemaInput$, () => DescribeSchemaOutput$
];
export var GraphTraverse$: StaticOperationSchema = [9, n1, _GT,
  { [_h]: ["POST", "/namespaces/{namespaceId}/graph/traverse", 200] }, () => GraphTraverseInput$, () => GraphTraverseOutput$
];
export var KBSearch$: StaticOperationSchema = [9, n1, _KBS,
  { [_h]: ["POST", "/namespaces/{namespaceId}/kb/search", 200] }, () => KBSearchInput$, () => KBSearchOutput$
];
export var Query$: StaticOperationSchema = [9, n1, _Q,
  { [_h]: ["POST", "/namespaces/{namespaceId}/query", 200] }, () => QueryInput$, () => QueryOutput$
];
export var TranslateSPARQL$: StaticOperationSchema = [9, n1, _TSPARQL,
  { [_h]: ["POST", "/namespaces/{namespaceId}/translate", 200] }, () => TranslateSPARQLInput$, () => TranslateSPARQLOutput$
];
