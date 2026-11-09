// smithy-typescript generated code
import { Sha256 } from "@aws-crypto/sha256-js";

import type { ControlPlaneServiceClientConfig } from "./ControlPlaneServiceClient";
import { getRuntimeConfig as getBrowserRuntimeConfig } from "./runtimeConfig.browser";

/**
 * @internal
 */
export const getRuntimeConfig = (config: ControlPlaneServiceClientConfig) => {
  const browserDefaults = getBrowserRuntimeConfig(config);
  return {
    ...browserDefaults,
    ...config,
    runtime: "react-native",
    sha256: config?.sha256 ?? Sha256,
  };
};
