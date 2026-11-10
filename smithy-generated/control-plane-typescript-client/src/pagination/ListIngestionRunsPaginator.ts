// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListIngestionRunsCommand,
  ListIngestionRunsCommandInput,
  ListIngestionRunsCommandOutput,
} from "../commands/ListIngestionRunsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListIngestionRuns: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListIngestionRunsCommandInput,
  ...rest: any[]
) => Paginator<ListIngestionRunsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListIngestionRunsCommandInput,
  ListIngestionRunsCommandOutput
>(ControlPlaneServiceClient, ListIngestionRunsCommand, "nextToken", "nextToken", "maxResults");
