// smithy-typescript generated code
import type { ExceptionOptionType as __ExceptionOptionType } from "@smithy/smithy-client";

import { DataLayerServiceServiceException as __BaseException } from "./DataLayerServiceServiceException";

/**
 * Returned with HTTP 500 when the service fails unexpectedly. The message is a
 * fixed, generic description; the underlying cause is logged, never returned.
 * @public
 */
export class InternalServerError extends __BaseException {
  readonly name = "InternalServerError" as const;
  readonly $fault = "server" as const;
  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<InternalServerError, __BaseException>) {
    super({
      name: "InternalServerError",
      $fault: "server",
      ...opts,
    });
    Object.setPrototypeOf(this, InternalServerError.prototype);
  }
}

/**
 * Returned with HTTP 503 when the service, or a required dependency (including
 * one it needs to handle the request safely), is temporarily unavailable. For
 * example, a create that
 * carries a `clientToken` fails closed with this error when the retry-safety
 * store cannot be reached, rather than risk running the create twice. Retry
 * the request (with the same `clientToken`) after a backoff.
 * @public
 */
export class ServiceUnavailableError extends __BaseException {
  readonly name = "ServiceUnavailableError" as const;
  readonly $fault = "server" as const;
  $retryable = {};
  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<ServiceUnavailableError, __BaseException>) {
    super({
      name: "ServiceUnavailableError",
      $fault: "server",
      ...opts,
    });
    Object.setPrototypeOf(this, ServiceUnavailableError.prototype);
  }
}

/**
 * Standard error structure
 * @public
 */
export class ValidationError extends __BaseException {
  readonly name = "ValidationError" as const;
  readonly $fault = "client" as const;
  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<ValidationError, __BaseException>) {
    super({
      name: "ValidationError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Returned with HTTP 403 when the caller lacks permission to perform the requested operation.
 * @public
 */
export class AccessDeniedError extends __BaseException {
  readonly name = "AccessDeniedError" as const;
  readonly $fault = "client" as const;
  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<AccessDeniedError, __BaseException>) {
    super({
      name: "AccessDeniedError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, AccessDeniedError.prototype);
  }
}

/**
 * Returned with HTTP 404 when the target namespace does not exist or is not
 * visible to the caller.
 * @public
 */
export class NamespaceNotFoundError extends __BaseException {
  readonly name = "NamespaceNotFoundError" as const;
  readonly $fault = "client" as const;
  /**
   * Identifier of the namespace that was not found.
   * @public
   */
  namespaceId?: string | undefined;

  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<NamespaceNotFoundError, __BaseException>) {
    super({
      name: "NamespaceNotFoundError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, NamespaceNotFoundError.prototype);
    this.namespaceId = opts.namespaceId;
  }
}

/**
 * Returned with HTTP 409 when the namespace has no published ontology, so the
 * query cannot be resolved against a schema yet.
 * @public
 */
export class OntologyNotPublishedError extends __BaseException {
  readonly name = "OntologyNotPublishedError" as const;
  readonly $fault = "client" as const;
  /**
   * Identifier of the namespace whose ontology is not published.
   * @public
   */
  namespaceId?: string | undefined;

  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<OntologyNotPublishedError, __BaseException>) {
    super({
      name: "OntologyNotPublishedError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, OntologyNotPublishedError.prototype);
    this.namespaceId = opts.namespaceId;
  }
}

/**
 * Returned with HTTP 429 when the caller exceeds the request rate limit;
 * `retryAfterSeconds` indicates how long to wait before retrying.
 * @public
 */
export class RateLimitExceededError extends __BaseException {
  readonly name = "RateLimitExceededError" as const;
  readonly $fault = "client" as const;
  /**
   * Number of seconds to wait before retrying the request.
   * @public
   */
  retryAfterSeconds?: number | undefined;

  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<RateLimitExceededError, __BaseException>) {
    super({
      name: "RateLimitExceededError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, RateLimitExceededError.prototype);
    this.retryAfterSeconds = opts.retryAfterSeconds;
  }
}

/**
 * Returned with HTTP 502 when a backing data source cannot be reached to
 * answer the query; `dataSourceId` identifies the unavailable source.
 * @public
 */
export class DataSourceUnavailableError extends __BaseException {
  readonly name = "DataSourceUnavailableError" as const;
  readonly $fault = "server" as const;
  /**
   * Identifier of the data source that could not be reached.
   * @public
   */
  dataSourceId?: string | undefined;

  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<DataSourceUnavailableError, __BaseException>) {
    super({
      name: "DataSourceUnavailableError",
      $fault: "server",
      ...opts,
    });
    Object.setPrototypeOf(this, DataSourceUnavailableError.prototype);
    this.dataSourceId = opts.dataSourceId;
  }
}

/**
 * Returned with HTTP 404 when a pinned tier produced no data for the query —
 * a "no results" outcome rather than a server error.
 * @public
 */
export class NoResultError extends __BaseException {
  readonly name = "NoResultError" as const;
  readonly $fault = "client" as const;
  /**
   * Pinned tier that produced no result (1 = metric match, 2 = structured query).
   * @public
   */
  tier?: number | undefined;

  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<NoResultError, __BaseException>) {
    super({
      name: "NoResultError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, NoResultError.prototype);
    this.tier = opts.tier;
  }
}

/**
 * Returned with HTTP 400 when a natural-language question cannot be translated
 * into an executable query against the ontology.
 * @public
 */
export class QueryTranslationError extends __BaseException {
  readonly name = "QueryTranslationError" as const;
  readonly $fault = "client" as const;
  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<QueryTranslationError, __BaseException>) {
    super({
      name: "QueryTranslationError",
      $fault: "client",
      ...opts,
    });
    Object.setPrototypeOf(this, QueryTranslationError.prototype);
  }
}

/**
 * Returned with HTTP 502 when the virtual knowledge graph fails to execute the
 * generated SPARQL query.
 *
 * Carries a fixed, client-safe message only. The failing query and the
 * backend's own error text are deliberately not returned: they name internal
 * schema objects and endpoints. Operators correlate a failure through the
 * request id instead.
 * @public
 */
export class VKGExecutionError extends __BaseException {
  readonly name = "VKGExecutionError" as const;
  readonly $fault = "server" as const;
  /**
   * @internal
   */
  constructor(opts: __ExceptionOptionType<VKGExecutionError, __BaseException>) {
    super({
      name: "VKGExecutionError",
      $fault: "server",
      ...opts,
    });
    Object.setPrototypeOf(this, VKGExecutionError.prototype);
  }
}
