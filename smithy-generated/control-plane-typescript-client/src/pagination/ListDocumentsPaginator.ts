// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListDocumentsCommand,
  ListDocumentsCommandInput,
  ListDocumentsCommandOutput,
} from "../commands/ListDocumentsCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListDocuments: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListDocumentsCommandInput,
  ...rest: any[]
) => Paginator<ListDocumentsCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListDocumentsCommandInput,
  ListDocumentsCommandOutput
>(ControlPlaneServiceClient, ListDocumentsCommand, "nextToken", "nextToken", "maxResults");
