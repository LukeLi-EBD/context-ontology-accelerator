// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListPrincipalGrantsCommand,
  ListPrincipalGrantsCommandInput,
  ListPrincipalGrantsCommandOutput,
} from "../commands/ListPrincipalGrantsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListPrincipalGrants: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListPrincipalGrantsCommandInput,
  ...rest: any[]
) => Paginator<ListPrincipalGrantsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListPrincipalGrantsCommandInput,
  ListPrincipalGrantsCommandOutput
>(ControlPlaneServiceClient, ListPrincipalGrantsCommand, "nextToken", "nextToken", "maxResults");
