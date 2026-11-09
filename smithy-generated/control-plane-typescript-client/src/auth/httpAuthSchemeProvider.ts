// smithy-typescript generated code
import { doesIdentityRequireRefresh, isIdentityExpired, memoizeIdentityProvider } from "@smithy/core";
import {
  type HandlerExecutionContext,
  type HttpAuthOption,
  type HttpAuthScheme,
  type HttpAuthSchemeParameters,
  type HttpAuthSchemeParametersProvider,
  type HttpAuthSchemeProvider,
  type Provider,
  TokenIdentity,
  TokenIdentityProvider,
} from "@smithy/types";
import { getSmithyContext, normalizeProvider } from "@smithy/util-middleware";

import type { ControlPlaneServiceClientResolvedConfig } from "../ControlPlaneServiceClient";

/**
 * @internal
 */
export interface ControlPlaneServiceHttpAuthSchemeParameters extends HttpAuthSchemeParameters {}

/**
 * @internal
 */
export interface ControlPlaneServiceHttpAuthSchemeParametersProvider
  extends HttpAuthSchemeParametersProvider<
    ControlPlaneServiceClientResolvedConfig,
    HandlerExecutionContext,
    ControlPlaneServiceHttpAuthSchemeParameters,
    object
  > {}

/**
 * @internal
 */
export const defaultControlPlaneServiceHttpAuthSchemeParametersProvider = async (
  config: ControlPlaneServiceClientResolvedConfig,
  context: HandlerExecutionContext,
  input: object
): Promise<ControlPlaneServiceHttpAuthSchemeParameters> => {
  return {
    operation: getSmithyContext(context).operation as string,
  };
};

function createSmithyApiHttpBearerAuthHttpAuthOption(authParameters: ControlPlaneServiceHttpAuthSchemeParameters): HttpAuthOption {
  return {
    schemeId: "smithy.api#httpBearerAuth",
  };
}

function createSmithyApiNoAuthHttpAuthOption(authParameters: ControlPlaneServiceHttpAuthSchemeParameters): HttpAuthOption {
  return {
    schemeId: "smithy.api#noAuth",
  };
}

/**
 * @internal
 */
export interface ControlPlaneServiceHttpAuthSchemeProvider
  extends HttpAuthSchemeProvider<ControlPlaneServiceHttpAuthSchemeParameters> {}

/**
 * @internal
 */
export const defaultControlPlaneServiceHttpAuthSchemeProvider: ControlPlaneServiceHttpAuthSchemeProvider = (authParameters) => {
  const options: HttpAuthOption[] = [];
  switch (authParameters.operation) {
    case "HealthCheck": {
      options.push(createSmithyApiHttpBearerAuthHttpAuthOption(authParameters));
      options.push(createSmithyApiNoAuthHttpAuthOption(authParameters));
      break;
    };
    default: {
      options.push(createSmithyApiHttpBearerAuthHttpAuthOption(authParameters));
    }
  }
  return options;
};

/**
 * @public
 */
export interface HttpAuthSchemeInputConfig {
  /**
   * A comma-separated list of case-sensitive auth scheme names.
   * An auth scheme name is a fully qualified auth scheme ID with the namespace prefix trimmed.
   * For example, the auth scheme with ID aws.auth#sigv4 is named sigv4.
   * @public
   */
  authSchemePreference?: string[] | Provider<string[]>;

  /**
   * Configuration of HttpAuthSchemes for a client which provides default identity providers and signers per auth scheme.
   * @internal
   */
  httpAuthSchemes?: HttpAuthScheme[];

  /**
   * Configuration of an HttpAuthSchemeProvider for a client which resolves which HttpAuthScheme to use.
   * @internal
   */
  httpAuthSchemeProvider?: ControlPlaneServiceHttpAuthSchemeProvider;
  /**
   * The token used to authenticate requests.
   */
  token?: TokenIdentity | TokenIdentityProvider;
}

/**
 * @internal
 */
export interface HttpAuthSchemeResolvedConfig {
  /**
   * A comma-separated list of case-sensitive auth scheme names.
   * An auth scheme name is a fully qualified auth scheme ID with the namespace prefix trimmed.
   * For example, the auth scheme with ID aws.auth#sigv4 is named sigv4.
   * @public
   */
  readonly authSchemePreference: Provider<string[]>;

  /**
   * Configuration of HttpAuthSchemes for a client which provides default identity providers and signers per auth scheme.
   * @internal
   */
  readonly httpAuthSchemes: HttpAuthScheme[];

  /**
   * Configuration of an HttpAuthSchemeProvider for a client which resolves which HttpAuthScheme to use.
   * @internal
   */
  readonly httpAuthSchemeProvider: ControlPlaneServiceHttpAuthSchemeProvider;
  /**
   * The token used to authenticate requests.
   */
  readonly token?: TokenIdentityProvider;
}

/**
 * @internal
 */
export const resolveHttpAuthSchemeConfig = <T>(
  config: T & HttpAuthSchemeInputConfig
): T & HttpAuthSchemeResolvedConfig => {
  const token = memoizeIdentityProvider(config.token, isIdentityExpired, doesIdentityRequireRefresh);
  return Object.assign(config, {
    authSchemePreference: normalizeProvider(config.authSchemePreference ?? []),
    token,
  }) as T & HttpAuthSchemeResolvedConfig;
};
