// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListProposalsCommand,
  ListProposalsCommandInput,
  ListProposalsCommandOutput,
} from "../commands/ListProposalsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListProposals: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListProposalsCommandInput,
  ...rest: any[]
) => Paginator<ListProposalsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListProposalsCommandInput,
  ListProposalsCommandOutput
>(ControlPlaneServiceClient, ListProposalsCommand, "nextToken", "nextToken", "maxResults");
