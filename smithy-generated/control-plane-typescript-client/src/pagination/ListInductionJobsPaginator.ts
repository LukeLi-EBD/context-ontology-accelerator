// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListInductionJobsCommand,
  ListInductionJobsCommandInput,
  ListInductionJobsCommandOutput,
} from "../commands/ListInductionJobsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListInductionJobs: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListInductionJobsCommandInput,
  ...rest: any[]
) => Paginator<ListInductionJobsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListInductionJobsCommandInput,
  ListInductionJobsCommandOutput
>(ControlPlaneServiceClient, ListInductionJobsCommand, "nextToken", "nextToken", "maxResults");
