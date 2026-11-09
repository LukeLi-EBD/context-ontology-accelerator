// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListPlatformGrantsCommand,
  ListPlatformGrantsCommandInput,
  ListPlatformGrantsCommandOutput,
} from "../commands/ListPlatformGrantsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListPlatformGrants: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListPlatformGrantsCommandInput,
  ...rest: any[]
) => Paginator<ListPlatformGrantsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListPlatformGrantsCommandInput,
  ListPlatformGrantsCommandOutput
>(ControlPlaneServiceClient, ListPlatformGrantsCommand, "nextToken", "nextToken", "maxResults");
