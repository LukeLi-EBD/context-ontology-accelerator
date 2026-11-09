// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListSourceScanJobsCommand,
  ListSourceScanJobsCommandInput,
  ListSourceScanJobsCommandOutput,
} from "../commands/ListSourceScanJobsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListSourceScanJobs: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListSourceScanJobsCommandInput,
  ...rest: any[]
) => Paginator<ListSourceScanJobsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListSourceScanJobsCommandInput,
  ListSourceScanJobsCommandOutput
>(ControlPlaneServiceClient, ListSourceScanJobsCommand, "nextToken", "nextToken", "maxResults");
