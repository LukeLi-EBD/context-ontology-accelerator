// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListSourceTablesCommand,
  ListSourceTablesCommandInput,
  ListSourceTablesCommandOutput,
} from "../commands/ListSourceTablesCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListSourceTables: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListSourceTablesCommandInput,
  ...rest: any[]
) => Paginator<ListSourceTablesCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListSourceTablesCommandInput,
  ListSourceTablesCommandOutput
>(ControlPlaneServiceClient, ListSourceTablesCommand, "nextToken", "nextToken", "maxResults");
