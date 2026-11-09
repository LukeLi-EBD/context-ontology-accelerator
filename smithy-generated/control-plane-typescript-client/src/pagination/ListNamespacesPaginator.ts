// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListNamespacesCommand,
  ListNamespacesCommandInput,
  ListNamespacesCommandOutput,
} from "../commands/ListNamespacesCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListNamespaces: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListNamespacesCommandInput,
  ...rest: any[]
) => Paginator<ListNamespacesCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListNamespacesCommandInput,
  ListNamespacesCommandOutput
>(ControlPlaneServiceClient, ListNamespacesCommand, "nextToken", "nextToken", "maxResults");
