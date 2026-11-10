// smithy-typescript generated code
import { createAggregatedClient } from "@smithy/smithy-client";
import type { HttpHandlerOptions as __HttpHandlerOptions } from "@smithy/types";

import {
  type CheckAnswerableCommandInput,
  type CheckAnswerableCommandOutput,
  CheckAnswerableCommand,
} from "./commands/CheckAnswerableCommand";
import {
  type DescribeSchemaCommandInput,
  type DescribeSchemaCommandOutput,
  DescribeSchemaCommand,
} from "./commands/DescribeSchemaCommand";
import {
  type GraphTraverseCommandInput,
  type GraphTraverseCommandOutput,
  GraphTraverseCommand,
} from "./commands/GraphTraverseCommand";
import { type KBSearchCommandInput, type KBSearchCommandOutput, KBSearchCommand } from "./commands/KBSearchCommand";
import { type QueryCommandInput, type QueryCommandOutput, QueryCommand } from "./commands/QueryCommand";
import { type RunSparqlCommandInput, type RunSparqlCommandOutput, RunSparqlCommand } from "./commands/RunSparqlCommand";
import {
  type TranslateSPARQLCommandInput,
  type TranslateSPARQLCommandOutput,
  TranslateSPARQLCommand,
} from "./commands/TranslateSPARQLCommand";
import { DataLayerServiceClient } from "./DataLayerServiceClient";

const commands = {
  CheckAnswerableCommand,
  DescribeSchemaCommand,
  GraphTraverseCommand,
  KBSearchCommand,
  QueryCommand,
  RunSparqlCommand,
  TranslateSPARQLCommand,
};

export interface DataLayerService {
  /**
   * @see {@link CheckAnswerableCommand}
   */
  checkAnswerable(
    args: CheckAnswerableCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CheckAnswerableCommandOutput>;
  checkAnswerable(
    args: CheckAnswerableCommandInput,
    cb: (err: any, data?: CheckAnswerableCommandOutput) => void
  ): void;
  checkAnswerable(
    args: CheckAnswerableCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CheckAnswerableCommandOutput) => void
  ): void;

  /**
   * @see {@link DescribeSchemaCommand}
   */
  describeSchema(
    args: DescribeSchemaCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeSchemaCommandOutput>;
  describeSchema(
    args: DescribeSchemaCommandInput,
    cb: (err: any, data?: DescribeSchemaCommandOutput) => void
  ): void;
  describeSchema(
    args: DescribeSchemaCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeSchemaCommandOutput) => void
  ): void;

  /**
   * @see {@link GraphTraverseCommand}
   */
  graphTraverse(
    args: GraphTraverseCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GraphTraverseCommandOutput>;
  graphTraverse(
    args: GraphTraverseCommandInput,
    cb: (err: any, data?: GraphTraverseCommandOutput) => void
  ): void;
  graphTraverse(
    args: GraphTraverseCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GraphTraverseCommandOutput) => void
  ): void;

  /**
   * @see {@link KBSearchCommand}
   */
  kBSearch(
    args: KBSearchCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<KBSearchCommandOutput>;
  kBSearch(
    args: KBSearchCommandInput,
    cb: (err: any, data?: KBSearchCommandOutput) => void
  ): void;
  kBSearch(
    args: KBSearchCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: KBSearchCommandOutput) => void
  ): void;

  /**
   * @see {@link QueryCommand}
   */
  query(
    args: QueryCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<QueryCommandOutput>;
  query(
    args: QueryCommandInput,
    cb: (err: any, data?: QueryCommandOutput) => void
  ): void;
  query(
    args: QueryCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: QueryCommandOutput) => void
  ): void;

  /**
   * @see {@link RunSparqlCommand}
   */
  runSparql(
    args: RunSparqlCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RunSparqlCommandOutput>;
  runSparql(
    args: RunSparqlCommandInput,
    cb: (err: any, data?: RunSparqlCommandOutput) => void
  ): void;
  runSparql(
    args: RunSparqlCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RunSparqlCommandOutput) => void
  ): void;

  /**
   * @see {@link TranslateSPARQLCommand}
   */
  translateSPARQL(
    args: TranslateSPARQLCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<TranslateSPARQLCommandOutput>;
  translateSPARQL(
    args: TranslateSPARQLCommandInput,
    cb: (err: any, data?: TranslateSPARQLCommandOutput) => void
  ): void;
  translateSPARQL(
    args: TranslateSPARQLCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: TranslateSPARQLCommandOutput) => void
  ): void;
}

/**
 * @public
 */
export class DataLayerService extends DataLayerServiceClient implements DataLayerService {}
createAggregatedClient(commands, DataLayerService);
