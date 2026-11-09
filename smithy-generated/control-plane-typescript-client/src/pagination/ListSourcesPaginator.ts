// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import { ListSourcesCommand, ListSourcesCommandInput, ListSourcesCommandOutput } from "../commands/ListSourcesCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListSources: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListSourcesCommandInput,
  ...rest: any[]
) => Paginator<ListSourcesCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListSourcesCommandInput,
  ListSourcesCommandOutput
>(ControlPlaneServiceClient, ListSourcesCommand, "nextToken", "nextToken", "maxResults");
