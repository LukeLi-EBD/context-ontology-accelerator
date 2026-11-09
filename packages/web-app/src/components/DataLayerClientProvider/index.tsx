// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {
  createContext,
  PropsWithChildren,
  useContext,
  useMemo,
} from "react";
import { DataLayerServiceClient } from "@coa/data-layer-client";
import { RuntimeConfigContext } from "../RuntimeContext";
import { OIDCProvider } from "@auth";

const DataLayerClientContext = createContext<
  DataLayerServiceClient | undefined
>(undefined);

export const useDataLayerClient = (): DataLayerServiceClient => {
  const ctx = useContext(DataLayerClientContext);
  if (!ctx)
    throw new Error(
      "useDataLayerClient must be used within DataLayerClientProvider",
    );
  return ctx;
};

/**
 * The data-layer contract (`Query`, `KBSearch`, …) shares the API Gateway
 * endpoint with the control plane; only the client class differs. Token
 * handling mirrors ControlPlaneClientProvider, including the ID token's
 * expiry so the SDK actually refreshes instead of caching the first token.
 */
export const DataLayerClientProvider: React.FC<PropsWithChildren> = ({
  children,
}) => {
  const runtimeContext = useContext(RuntimeConfigContext);
  const apiEndpoint = runtimeContext?.apiEndpoint;
  const oidcConfig = runtimeContext?.oidcConfig;

  const client = useMemo(() => {
    if (!apiEndpoint || !oidcConfig) return undefined;
    const provider = OIDCProvider.build(oidcConfig);
    return new DataLayerServiceClient({
      endpoint: apiEndpoint.replace(/\/$/, ""),
      token: async () => {
        const token = await provider.getIdToken();
        if (!token) throw new Error("Failed to retrieve authentication token");
        const user = await provider.getUser();
        const expiration =
          user?.profile?.exp !== undefined
            ? new Date(user.profile.exp * 1000)
            : undefined;
        return { token, expiration };
      },
    });
  }, [apiEndpoint, oidcConfig]);

  return (
    <DataLayerClientContext.Provider value={client}>
      {children}
    </DataLayerClientContext.Provider>
  );
};
