// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListInducedDatasourcesCommand,
  ListInducedDatasourcesCommandInput,
  ListInducedDatasourcesCommandOutput,
} from "../commands/ListInducedDatasourcesCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListInducedDatasources: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListInducedDatasourcesCommandInput,
  ...rest: any[]
) => Paginator<ListInducedDatasourcesCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListInducedDatasourcesCommandInput,
  ListInducedDatasourcesCommandOutput
>(ControlPlaneServiceClient, ListInducedDatasourcesCommand, "nextToken", "nextToken", "maxResults");
