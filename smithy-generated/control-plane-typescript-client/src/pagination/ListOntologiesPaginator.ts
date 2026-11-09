// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListOntologiesCommand,
  ListOntologiesCommandInput,
  ListOntologiesCommandOutput,
} from "../commands/ListOntologiesCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListOntologies: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListOntologiesCommandInput,
  ...rest: any[]
) => Paginator<ListOntologiesCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListOntologiesCommandInput,
  ListOntologiesCommandOutput
>(ControlPlaneServiceClient, ListOntologiesCommand, "nextToken", "nextToken", "maxResults");
