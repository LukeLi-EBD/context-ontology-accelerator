// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Local development `@auth` implementation.
 *
 * This file is NOT used by the production bundle. The local dev vite config
 * aliases `@auth` to `.dev-local/auth-stub`, and `doc/coa-x/10-本地起栈.ps1`
 * regenerates that stub so it re-exports this module.
 *
 * Unlike the previous fixed-token stub, this provider obtains a real, expiring
 * RS256 token from the local bridge (`POST /local/auth/token`), which the
 * bridge verifies on every request exactly like the deployed authorizer. If
 * the token endpoint is unreachable or rejects the request, the provider
 * throws — it never falls back to a fake identity.
 */

export interface OidcConfig {
  authority: string;
  clientId: string;
  onLoginRedirectPath?: string;
  onLogoutRedirectPath?: string;
}

interface RuntimeConfig {
  apiEndpoint?: string;
  localAuthUser?: string;
}

interface CachedToken {
  token: string;
  expiresAt: number;
}

const DEFAULT_DEV_USER = "local-dev@example.invalid";
const EXPIRY_SKEW_MS = 60_000;

let runtimeConfigPromise: Promise<RuntimeConfig> | undefined;
let cachedToken: CachedToken | undefined;

function loadRuntimeConfig(): Promise<RuntimeConfig> {
  if (!runtimeConfigPromise) {
    runtimeConfigPromise = fetch("/runtime-config.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<RuntimeConfig>;
      })
      .catch((error: unknown) => {
        runtimeConfigPromise = undefined;
        throw new Error(
          `Local dev auth: cannot read /runtime-config.json (${String(error)})`,
        );
      });
  }
  return runtimeConfigPromise;
}

async function requestToken(): Promise<CachedToken> {
  const config = await loadRuntimeConfig();
  const endpoint = (config.apiEndpoint ?? "").replace(/\/$/, "");
  if (!endpoint) {
    throw new Error(
      "Local dev auth: runtime-config.json has no apiEndpoint; the bridge (COA_LOCAL_DEV_AUTH=on) is required",
    );
  }
  const response = await fetch(`${endpoint}/local/auth/token`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: config.localAuthUser ?? DEFAULT_DEV_USER }),
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(
      `Local dev auth: ${endpoint}/local/auth/token returned ${response.status} ${body}`,
    );
  }
  const payload = (await response.json()) as {
    accessToken?: string;
    expiresIn?: number;
  };
  if (!payload.accessToken) {
    throw new Error("Local dev auth: token response has no accessToken");
  }
  const ttlMs = (payload.expiresIn ?? 3600) * 1000;
  return { token: payload.accessToken, expiresAt: Date.now() + ttlMs };
}

async function getDevToken(): Promise<string> {
  if (cachedToken && cachedToken.expiresAt - EXPIRY_SKEW_MS > Date.now()) {
    return cachedToken.token;
  }
  cachedToken = await requestToken();
  return cachedToken.token;
}

export class OIDCProvider {
  static build(_config: OidcConfig): OIDCProvider {
    return new OIDCProvider();
  }

  async getUser(): Promise<{
    profile: { sub: string; email: string };
    expires_at: number;
  } | null> {
    const token = await getDevToken();
    const config = await loadRuntimeConfig();
    return {
      profile: {
        sub: config.localAuthUser ?? DEFAULT_DEV_USER,
        email: config.localAuthUser ?? DEFAULT_DEV_USER,
      },
      expires_at: Math.floor((cachedToken?.expiresAt ?? Date.now()) / 1000),
    };
  }

  async getIdToken(): Promise<string> {
    return getDevToken();
  }

  async getAccessToken(): Promise<string> {
    return getDevToken();
  }

  async authenticate(): Promise<void> {
    await getDevToken();
  }

  async signOut(): Promise<void> {
    cachedToken = undefined;
  }
}

export const UserProvider = ({ children }: { children: unknown }) =>
  children as never;

export const useUser = () => ({
  user: {
    userid: "local-dev",
    name: "Local Dev",
    email: DEFAULT_DEV_USER,
    groups: [],
  },
  error: undefined,
  logout: async () => {
    cachedToken = undefined;
  },
});
