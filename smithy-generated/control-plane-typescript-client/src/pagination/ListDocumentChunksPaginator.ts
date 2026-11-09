// smithy-typescript generated code
import { createPaginator } from "@smithy/core";
import type { Paginator } from "@smithy/types";

import {
  ListDocumentChunksCommand,
  ListDocumentChunksCommandInput,
  ListDocumentChunksCommandOutput,
} from "../commands/ListDocumentChunksCommand";
import { ControlPlaneServiceClient } from "../ControlPlaneServiceClient";
import type { ControlPlaneServicePaginationConfiguration } from "./Interfaces";

/**
 * @public
 */
export const paginateListDocumentChunks: (
  config: ControlPlaneServicePaginationConfiguration,
  input: ListDocumentChunksCommandInput,
  ...rest: any[]
) => Paginator<ListDocumentChunksCommandOutput> = createPaginator<
  ControlPlaneServicePaginationConfiguration,
  ListDocumentChunksCommandInput,
  ListDocumentChunksCommandOutput
>(ControlPlaneServiceClient, ListDocumentChunksCommand, "nextToken", "nextToken", "maxResults");
