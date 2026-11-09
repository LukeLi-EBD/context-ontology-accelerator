// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import { ListMetricsCommand, ListMetricsCommandInput, ListMetricsCommandOutput } from "../commands/ListMetricsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListMetrics: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListMetricsCommandInput,
  ...rest: any[]
) => Paginator<ListMetricsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListMetricsCommandInput,
  ListMetricsCommandOutput
>(ControlPlaneServiceClient, ListMetricsCommand, "nextToken", "nextToken", "maxResults");
