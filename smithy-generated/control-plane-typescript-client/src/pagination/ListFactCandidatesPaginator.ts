// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListFactCandidatesCommand,
  ListFactCandidatesCommandInput,
  ListFactCandidatesCommandOutput,
} from "../commands/ListFactCandidatesCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListFactCandidates: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListFactCandidatesCommandInput,
  ...rest: any[]
) => Paginator<ListFactCandidatesCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListFactCandidatesCommandInput,
  ListFactCandidatesCommandOutput
>(ControlPlaneServiceClient, ListFactCandidatesCommand, "nextToken", "nextToken", "maxResults");
