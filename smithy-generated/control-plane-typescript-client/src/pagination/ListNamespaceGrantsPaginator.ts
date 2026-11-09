// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListNamespaceGrantsCommand,
  ListNamespaceGrantsCommandInput,
  ListNamespaceGrantsCommandOutput,
} from "../commands/ListNamespaceGrantsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListNamespaceGrants: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListNamespaceGrantsCommandInput,
  ...rest: any[]
) => Paginator<ListNamespaceGrantsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListNamespaceGrantsCommandInput,
  ListNamespaceGrantsCommandOutput
>(ControlPlaneServiceClient, ListNamespaceGrantsCommand, "nextToken", "nextToken", "maxResults");
