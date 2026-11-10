// smithy-typescript generated code
import { createAggregatedClient } from "@smithy/smithy-client";
import type { HttpHandlerOptions as __HttpHandlerOptions, PaginationConfiguration, Paginator } from "@smithy/types";

import {
  type AcceptProposalCommandInput,
  type AcceptProposalCommandOutput,
  AcceptProposalCommand,
} from "./commands/AcceptProposalCommand";
import {
  type ApproveFactCandidateCommandInput,
  type ApproveFactCandidateCommandOutput,
  ApproveFactCandidateCommand,
} from "./commands/ApproveFactCandidateCommand";
import {
  type ApproveSourceCommandInput,
  type ApproveSourceCommandOutput,
  ApproveSourceCommand,
} from "./commands/ApproveSourceCommand";
import {
  type BulkDeleteMetricsCommandInput,
  type BulkDeleteMetricsCommandOutput,
  BulkDeleteMetricsCommand,
} from "./commands/BulkDeleteMetricsCommand";
import {
  type CancelProposalCommandInput,
  type CancelProposalCommandOutput,
  CancelProposalCommand,
} from "./commands/CancelProposalCommand";
import {
  type CompileConstraintsCommandInput,
  type CompileConstraintsCommandOutput,
  CompileConstraintsCommand,
} from "./commands/CompileConstraintsCommand";
import {
  type CreateGrantCommandInput,
  type CreateGrantCommandOutput,
  CreateGrantCommand,
} from "./commands/CreateGrantCommand";
import {
  type CreateMetricCommandInput,
  type CreateMetricCommandOutput,
  CreateMetricCommand,
} from "./commands/CreateMetricCommand";
import {
  type CreateNamespaceCommandInput,
  type CreateNamespaceCommandOutput,
  CreateNamespaceCommand,
} from "./commands/CreateNamespaceCommand";
import {
  type CreatePlatformGrantCommandInput,
  type CreatePlatformGrantCommandOutput,
  CreatePlatformGrantCommand,
} from "./commands/CreatePlatformGrantCommand";
import {
  type CreateSourceCommandInput,
  type CreateSourceCommandOutput,
  CreateSourceCommand,
} from "./commands/CreateSourceCommand";
import {
  type DeleteGrantCommandInput,
  type DeleteGrantCommandOutput,
  DeleteGrantCommand,
} from "./commands/DeleteGrantCommand";
import {
  type DeleteMetricCommandInput,
  type DeleteMetricCommandOutput,
  DeleteMetricCommand,
} from "./commands/DeleteMetricCommand";
import {
  type DeleteNamespaceCommandInput,
  type DeleteNamespaceCommandOutput,
  DeleteNamespaceCommand,
} from "./commands/DeleteNamespaceCommand";
import {
  type DeleteOntologyCommandInput,
  type DeleteOntologyCommandOutput,
  DeleteOntologyCommand,
} from "./commands/DeleteOntologyCommand";
import {
  type DeletePlatformGrantCommandInput,
  type DeletePlatformGrantCommandOutput,
  DeletePlatformGrantCommand,
} from "./commands/DeletePlatformGrantCommand";
import {
  type DeleteSourceCommandInput,
  type DeleteSourceCommandOutput,
  DeleteSourceCommand,
} from "./commands/DeleteSourceCommand";
import {
  type DownloadOntologyCommandInput,
  type DownloadOntologyCommandOutput,
  DownloadOntologyCommand,
} from "./commands/DownloadOntologyCommand";
import { type ExportOsiCommandInput, type ExportOsiCommandOutput, ExportOsiCommand } from "./commands/ExportOsiCommand";
import {
  type FetchOntologyCommandInput,
  type FetchOntologyCommandOutput,
  FetchOntologyCommand,
} from "./commands/FetchOntologyCommand";
import {
  type GetCanvasManifestCommandInput,
  type GetCanvasManifestCommandOutput,
  GetCanvasManifestCommand,
} from "./commands/GetCanvasManifestCommand";
import {
  type GetEntityEmbeddingsCommandInput,
  type GetEntityEmbeddingsCommandOutput,
  GetEntityEmbeddingsCommand,
} from "./commands/GetEntityEmbeddingsCommand";
import {
  type GetGraphClassCommandInput,
  type GetGraphClassCommandOutput,
  GetGraphClassCommand,
} from "./commands/GetGraphClassCommand";
import {
  type GetGraphDatatypePropertyCommandInput,
  type GetGraphDatatypePropertyCommandOutput,
  GetGraphDatatypePropertyCommand,
} from "./commands/GetGraphDatatypePropertyCommand";
import {
  type GetGraphObjectPropertyCommandInput,
  type GetGraphObjectPropertyCommandOutput,
  GetGraphObjectPropertyCommand,
} from "./commands/GetGraphObjectPropertyCommand";
import {
  type GetImportJobCommandInput,
  type GetImportJobCommandOutput,
  GetImportJobCommand,
} from "./commands/GetImportJobCommand";
import {
  type GetInductionJobCommandInput,
  type GetInductionJobCommandOutput,
  GetInductionJobCommand,
} from "./commands/GetInductionJobCommand";
import {
  type GetInferConstraintsJobCommandInput,
  type GetInferConstraintsJobCommandOutput,
  GetInferConstraintsJobCommand,
} from "./commands/GetInferConstraintsJobCommand";
import {
  type GetIngestStatusCommandInput,
  type GetIngestStatusCommandOutput,
  GetIngestStatusCommand,
} from "./commands/GetIngestStatusCommand";
import { type GetMetricCommandInput, type GetMetricCommandOutput, GetMetricCommand } from "./commands/GetMetricCommand";
import {
  type GetNamespaceCommandInput,
  type GetNamespaceCommandOutput,
  GetNamespaceCommand,
} from "./commands/GetNamespaceCommand";
import {
  type GetNamespaceRoleCommandInput,
  type GetNamespaceRoleCommandOutput,
  GetNamespaceRoleCommand,
} from "./commands/GetNamespaceRoleCommand";
import {
  type GetOntologyCommandInput,
  type GetOntologyCommandOutput,
  GetOntologyCommand,
} from "./commands/GetOntologyCommand";
import {
  type GetOntologyOverviewCommandInput,
  type GetOntologyOverviewCommandOutput,
  GetOntologyOverviewCommand,
} from "./commands/GetOntologyOverviewCommand";
import {
  type GetOntologyUploadUrlCommandInput,
  type GetOntologyUploadUrlCommandOutput,
  GetOntologyUploadUrlCommand,
} from "./commands/GetOntologyUploadUrlCommand";
import {
  type GetOsiUploadUrlCommandInput,
  type GetOsiUploadUrlCommandOutput,
  GetOsiUploadUrlCommand,
} from "./commands/GetOsiUploadUrlCommand";
import {
  type GetProposalCommandInput,
  type GetProposalCommandOutput,
  GetProposalCommand,
} from "./commands/GetProposalCommand";
import {
  type GetProposalUploadUrlsCommandInput,
  type GetProposalUploadUrlsCommandOutput,
  GetProposalUploadUrlsCommand,
} from "./commands/GetProposalUploadUrlsCommand";
import {
  type GetProposalValidationJobCommandInput,
  type GetProposalValidationJobCommandOutput,
  GetProposalValidationJobCommand,
} from "./commands/GetProposalValidationJobCommand";
import { type GetSourceCommandInput, type GetSourceCommandOutput, GetSourceCommand } from "./commands/GetSourceCommand";
import {
  type GetSourceScanJobCommandInput,
  type GetSourceScanJobCommandOutput,
  GetSourceScanJobCommand,
} from "./commands/GetSourceScanJobCommand";
import {
  type GetSourceTableCommandInput,
  type GetSourceTableCommandOutput,
  GetSourceTableCommand,
} from "./commands/GetSourceTableCommand";
import {
  type GetSourceUploadUrlsCommandInput,
  type GetSourceUploadUrlsCommandOutput,
  GetSourceUploadUrlsCommand,
} from "./commands/GetSourceUploadUrlsCommand";
import {
  type GetSystemHealthCommandInput,
  type GetSystemHealthCommandOutput,
  GetSystemHealthCommand,
} from "./commands/GetSystemHealthCommand";
import {
  type GraphSearchCommandInput,
  type GraphSearchCommandOutput,
  GraphSearchCommand,
} from "./commands/GraphSearchCommand";
import {
  type HealthCheckCommandInput,
  type HealthCheckCommandOutput,
  HealthCheckCommand,
} from "./commands/HealthCheckCommand";
import { type ImportOsiCommandInput, type ImportOsiCommandOutput, ImportOsiCommand } from "./commands/ImportOsiCommand";
import {
  type InferConstraintsCommandInput,
  type InferConstraintsCommandOutput,
  InferConstraintsCommand,
} from "./commands/InferConstraintsCommand";
import {
  type IngestOntologyFromS3CommandInput,
  type IngestOntologyFromS3CommandOutput,
  IngestOntologyFromS3Command,
} from "./commands/IngestOntologyFromS3Command";
import {
  type KeepRescanRemovalCommandInput,
  type KeepRescanRemovalCommandOutput,
  KeepRescanRemovalCommand,
} from "./commands/KeepRescanRemovalCommand";
import {
  type ListDocumentChunksCommandInput,
  type ListDocumentChunksCommandOutput,
  ListDocumentChunksCommand,
} from "./commands/ListDocumentChunksCommand";
import {
  type ListDocumentsCommandInput,
  type ListDocumentsCommandOutput,
  ListDocumentsCommand,
} from "./commands/ListDocumentsCommand";
import {
  type ListFactCandidatesCommandInput,
  type ListFactCandidatesCommandOutput,
  ListFactCandidatesCommand,
} from "./commands/ListFactCandidatesCommand";
import {
  type ListFoundationalOntologiesCommandInput,
  type ListFoundationalOntologiesCommandOutput,
  ListFoundationalOntologiesCommand,
} from "./commands/ListFoundationalOntologiesCommand";
import {
  type ListInducedDatasourcesCommandInput,
  type ListInducedDatasourcesCommandOutput,
  ListInducedDatasourcesCommand,
} from "./commands/ListInducedDatasourcesCommand";
import {
  type ListInductionJobsCommandInput,
  type ListInductionJobsCommandOutput,
  ListInductionJobsCommand,
} from "./commands/ListInductionJobsCommand";
import {
  type ListMetricsCommandInput,
  type ListMetricsCommandOutput,
  ListMetricsCommand,
} from "./commands/ListMetricsCommand";
import {
  type ListNamespaceGrantsCommandInput,
  type ListNamespaceGrantsCommandOutput,
  ListNamespaceGrantsCommand,
} from "./commands/ListNamespaceGrantsCommand";
import {
  type ListNamespaceRolesCommandInput,
  type ListNamespaceRolesCommandOutput,
  ListNamespaceRolesCommand,
} from "./commands/ListNamespaceRolesCommand";
import {
  type ListNamespacesCommandInput,
  type ListNamespacesCommandOutput,
  ListNamespacesCommand,
} from "./commands/ListNamespacesCommand";
import {
  type ListOntologiesCommandInput,
  type ListOntologiesCommandOutput,
  ListOntologiesCommand,
} from "./commands/ListOntologiesCommand";
import {
  type ListPlatformGrantsCommandInput,
  type ListPlatformGrantsCommandOutput,
  ListPlatformGrantsCommand,
} from "./commands/ListPlatformGrantsCommand";
import {
  type ListPlatformRolesCommandInput,
  type ListPlatformRolesCommandOutput,
  ListPlatformRolesCommand,
} from "./commands/ListPlatformRolesCommand";
import {
  type ListPrincipalGrantsCommandInput,
  type ListPrincipalGrantsCommandOutput,
  ListPrincipalGrantsCommand,
} from "./commands/ListPrincipalGrantsCommand";
import {
  type ListProposalsCommandInput,
  type ListProposalsCommandOutput,
  ListProposalsCommand,
} from "./commands/ListProposalsCommand";
import {
  type ListSourceScanJobsCommandInput,
  type ListSourceScanJobsCommandOutput,
  ListSourceScanJobsCommand,
} from "./commands/ListSourceScanJobsCommand";
import {
  type ListSourcesCommandInput,
  type ListSourcesCommandOutput,
  ListSourcesCommand,
} from "./commands/ListSourcesCommand";
import {
  type ListSourceTablesCommandInput,
  type ListSourceTablesCommandOutput,
  ListSourceTablesCommand,
} from "./commands/ListSourceTablesCommand";
import {
  type ListStatementsCommandInput,
  type ListStatementsCommandOutput,
  ListStatementsCommand,
} from "./commands/ListStatementsCommand";
import {
  type LoadFoundationalOntologyCommandInput,
  type LoadFoundationalOntologyCommandOutput,
  LoadFoundationalOntologyCommand,
} from "./commands/LoadFoundationalOntologyCommand";
import {
  type PutSourceEventRescanCommandInput,
  type PutSourceEventRescanCommandOutput,
  PutSourceEventRescanCommand,
} from "./commands/PutSourceEventRescanCommand";
import {
  type PutSourceRescanScheduleCommandInput,
  type PutSourceRescanScheduleCommandOutput,
  PutSourceRescanScheduleCommand,
} from "./commands/PutSourceRescanScheduleCommand";
import {
  type RejectFactCandidateCommandInput,
  type RejectFactCandidateCommandOutput,
  RejectFactCandidateCommand,
} from "./commands/RejectFactCandidateCommand";
import {
  type RejectProposalsCommandInput,
  type RejectProposalsCommandOutput,
  RejectProposalsCommand,
} from "./commands/RejectProposalsCommand";
import {
  type RejectSourceCommandInput,
  type RejectSourceCommandOutput,
  RejectSourceCommand,
} from "./commands/RejectSourceCommand";
import {
  type RepairProposalDatatypesCommandInput,
  type RepairProposalDatatypesCommandOutput,
  RepairProposalDatatypesCommand,
} from "./commands/RepairProposalDatatypesCommand";
import {
  type RescanSourceCommandInput,
  type RescanSourceCommandOutput,
  RescanSourceCommand,
} from "./commands/RescanSourceCommand";
import {
  type ReviewSourceColumnCommandInput,
  type ReviewSourceColumnCommandOutput,
  ReviewSourceColumnCommand,
} from "./commands/ReviewSourceColumnCommand";
import {
  type ReviewSourceTableCommandInput,
  type ReviewSourceTableCommandOutput,
  ReviewSourceTableCommand,
} from "./commands/ReviewSourceTableCommand";
import {
  type SearchEmbeddingsCommandInput,
  type SearchEmbeddingsCommandOutput,
  SearchEmbeddingsCommand,
} from "./commands/SearchEmbeddingsCommand";
import {
  type StartInductionCommandInput,
  type StartInductionCommandOutput,
  StartInductionCommand,
} from "./commands/StartInductionCommand";
import {
  type UpdateMetricCommandInput,
  type UpdateMetricCommandOutput,
  UpdateMetricCommand,
} from "./commands/UpdateMetricCommand";
import {
  type UpdateNamespaceCommandInput,
  type UpdateNamespaceCommandOutput,
  UpdateNamespaceCommand,
} from "./commands/UpdateNamespaceCommand";
import {
  type UpdateNamespaceStatusCommandInput,
  type UpdateNamespaceStatusCommandOutput,
  UpdateNamespaceStatusCommand,
} from "./commands/UpdateNamespaceStatusCommand";
import {
  type UpdateProposalCommandInput,
  type UpdateProposalCommandOutput,
  UpdateProposalCommand,
} from "./commands/UpdateProposalCommand";
import {
  type UpdateSourceColumnMetadataCommandInput,
  type UpdateSourceColumnMetadataCommandOutput,
  UpdateSourceColumnMetadataCommand,
} from "./commands/UpdateSourceColumnMetadataCommand";
import {
  type UpdateSourceMetadataCommandInput,
  type UpdateSourceMetadataCommandOutput,
  UpdateSourceMetadataCommand,
} from "./commands/UpdateSourceMetadataCommand";
import {
  type UpdateSourceTableKeysCommandInput,
  type UpdateSourceTableKeysCommandOutput,
  UpdateSourceTableKeysCommand,
} from "./commands/UpdateSourceTableKeysCommand";
import {
  type UpdateSourceTableMetadataCommandInput,
  type UpdateSourceTableMetadataCommandOutput,
  UpdateSourceTableMetadataCommand,
} from "./commands/UpdateSourceTableMetadataCommand";
import {
  type UploadDocumentCommandInput,
  type UploadDocumentCommandOutput,
  UploadDocumentCommand,
} from "./commands/UploadDocumentCommand";
import {
  type UploadOntologyCommandInput,
  type UploadOntologyCommandOutput,
  UploadOntologyCommand,
} from "./commands/UploadOntologyCommand";
import {
  type ValidateMetricCommandInput,
  type ValidateMetricCommandOutput,
  ValidateMetricCommand,
} from "./commands/ValidateMetricCommand";
import {
  type ValidateProposalCommandInput,
  type ValidateProposalCommandOutput,
  ValidateProposalCommand,
} from "./commands/ValidateProposalCommand";
import { ControlPlaneServiceClient } from "./ControlPlaneServiceClient";
import { paginateListDocumentChunks } from "./pagination/ListDocumentChunksPaginator";
import { paginateListDocuments } from "./pagination/ListDocumentsPaginator";
import { paginateListFactCandidates } from "./pagination/ListFactCandidatesPaginator";
import { paginateListInducedDatasources } from "./pagination/ListInducedDatasourcesPaginator";
import { paginateListInductionJobs } from "./pagination/ListInductionJobsPaginator";
import { paginateListMetrics } from "./pagination/ListMetricsPaginator";
import { paginateListNamespaceGrants } from "./pagination/ListNamespaceGrantsPaginator";
import { paginateListNamespaces } from "./pagination/ListNamespacesPaginator";
import { paginateListOntologies } from "./pagination/ListOntologiesPaginator";
import { paginateListPlatformGrants } from "./pagination/ListPlatformGrantsPaginator";
import { paginateListPrincipalGrants } from "./pagination/ListPrincipalGrantsPaginator";
import { paginateListProposals } from "./pagination/ListProposalsPaginator";
import { paginateListSourceScanJobs } from "./pagination/ListSourceScanJobsPaginator";
import { paginateListSources } from "./pagination/ListSourcesPaginator";
import { paginateListSourceTables } from "./pagination/ListSourceTablesPaginator";

const commands = {
  GetSystemHealthCommand,
  HealthCheckCommand,
  ApproveFactCandidateCommand,
  ListDocumentChunksCommand,
  ListDocumentsCommand,
  ListFactCandidatesCommand,
  RejectFactCandidateCommand,
  UploadDocumentCommand,
  GetEntityEmbeddingsCommand,
  SearchEmbeddingsCommand,
  CreateGrantCommand,
  CreatePlatformGrantCommand,
  DeleteGrantCommand,
  DeletePlatformGrantCommand,
  ListNamespaceGrantsCommand,
  ListPlatformGrantsCommand,
  ListPrincipalGrantsCommand,
  BulkDeleteMetricsCommand,
  CreateMetricCommand,
  DeleteMetricCommand,
  ExportOsiCommand,
  GetImportJobCommand,
  GetMetricCommand,
  GetOsiUploadUrlCommand,
  ImportOsiCommand,
  ListMetricsCommand,
  UpdateMetricCommand,
  ValidateMetricCommand,
  CreateNamespaceCommand,
  DeleteNamespaceCommand,
  GetNamespaceCommand,
  ListNamespacesCommand,
  UpdateNamespaceCommand,
  UpdateNamespaceStatusCommand,
  DeleteOntologyCommand,
  DownloadOntologyCommand,
  FetchOntologyCommand,
  GetCanvasManifestCommand,
  GetGraphClassCommand,
  GetGraphDatatypePropertyCommand,
  GetGraphObjectPropertyCommand,
  GetIngestStatusCommand,
  GetOntologyCommand,
  GetOntologyOverviewCommand,
  GetOntologyUploadUrlCommand,
  GraphSearchCommand,
  IngestOntologyFromS3Command,
  ListOntologiesCommand,
  ListStatementsCommand,
  UploadOntologyCommand,
  AcceptProposalCommand,
  CancelProposalCommand,
  CompileConstraintsCommand,
  GetInductionJobCommand,
  GetInferConstraintsJobCommand,
  GetProposalCommand,
  GetProposalUploadUrlsCommand,
  GetProposalValidationJobCommand,
  InferConstraintsCommand,
  ListFoundationalOntologiesCommand,
  ListInducedDatasourcesCommand,
  ListInductionJobsCommand,
  ListProposalsCommand,
  LoadFoundationalOntologyCommand,
  RejectProposalsCommand,
  RepairProposalDatatypesCommand,
  StartInductionCommand,
  UpdateProposalCommand,
  ValidateProposalCommand,
  GetNamespaceRoleCommand,
  ListNamespaceRolesCommand,
  ListPlatformRolesCommand,
  ApproveSourceCommand,
  CreateSourceCommand,
  DeleteSourceCommand,
  GetSourceCommand,
  GetSourceScanJobCommand,
  GetSourceTableCommand,
  GetSourceUploadUrlsCommand,
  KeepRescanRemovalCommand,
  ListSourcesCommand,
  ListSourceScanJobsCommand,
  ListSourceTablesCommand,
  PutSourceEventRescanCommand,
  PutSourceRescanScheduleCommand,
  RejectSourceCommand,
  RescanSourceCommand,
  ReviewSourceColumnCommand,
  ReviewSourceTableCommand,
  UpdateSourceColumnMetadataCommand,
  UpdateSourceMetadataCommand,
  UpdateSourceTableKeysCommand,
  UpdateSourceTableMetadataCommand,
};
const paginators = {
  paginateListDocumentChunks,
  paginateListDocuments,
  paginateListFactCandidates,
  paginateListNamespaceGrants,
  paginateListPlatformGrants,
  paginateListPrincipalGrants,
  paginateListMetrics,
  paginateListNamespaces,
  paginateListOntologies,
  paginateListInducedDatasources,
  paginateListInductionJobs,
  paginateListProposals,
  paginateListSources,
  paginateListSourceScanJobs,
  paginateListSourceTables,
};

export interface ControlPlaneService {
  /**
   * @see {@link GetSystemHealthCommand}
   */
  getSystemHealth(): Promise<GetSystemHealthCommandOutput>;
  getSystemHealth(
    args: GetSystemHealthCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSystemHealthCommandOutput>;
  getSystemHealth(
    args: GetSystemHealthCommandInput,
    cb: (err: any, data?: GetSystemHealthCommandOutput) => void
  ): void;
  getSystemHealth(
    args: GetSystemHealthCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSystemHealthCommandOutput) => void
  ): void;

  /**
   * @see {@link HealthCheckCommand}
   */
  healthCheck(): Promise<HealthCheckCommandOutput>;
  healthCheck(
    args: HealthCheckCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<HealthCheckCommandOutput>;
  healthCheck(
    args: HealthCheckCommandInput,
    cb: (err: any, data?: HealthCheckCommandOutput) => void
  ): void;
  healthCheck(
    args: HealthCheckCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: HealthCheckCommandOutput) => void
  ): void;

  /**
   * @see {@link ApproveFactCandidateCommand}
   */
  approveFactCandidate(
    args: ApproveFactCandidateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ApproveFactCandidateCommandOutput>;
  approveFactCandidate(
    args: ApproveFactCandidateCommandInput,
    cb: (err: any, data?: ApproveFactCandidateCommandOutput) => void
  ): void;
  approveFactCandidate(
    args: ApproveFactCandidateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ApproveFactCandidateCommandOutput) => void
  ): void;

  /**
   * @see {@link ListDocumentChunksCommand}
   */
  listDocumentChunks(
    args: ListDocumentChunksCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListDocumentChunksCommandOutput>;
  listDocumentChunks(
    args: ListDocumentChunksCommandInput,
    cb: (err: any, data?: ListDocumentChunksCommandOutput) => void
  ): void;
  listDocumentChunks(
    args: ListDocumentChunksCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListDocumentChunksCommandOutput) => void
  ): void;

  /**
   * @see {@link ListDocumentsCommand}
   */
  listDocuments(
    args: ListDocumentsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListDocumentsCommandOutput>;
  listDocuments(
    args: ListDocumentsCommandInput,
    cb: (err: any, data?: ListDocumentsCommandOutput) => void
  ): void;
  listDocuments(
    args: ListDocumentsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListDocumentsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListFactCandidatesCommand}
   */
  listFactCandidates(
    args: ListFactCandidatesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListFactCandidatesCommandOutput>;
  listFactCandidates(
    args: ListFactCandidatesCommandInput,
    cb: (err: any, data?: ListFactCandidatesCommandOutput) => void
  ): void;
  listFactCandidates(
    args: ListFactCandidatesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListFactCandidatesCommandOutput) => void
  ): void;

  /**
   * @see {@link RejectFactCandidateCommand}
   */
  rejectFactCandidate(
    args: RejectFactCandidateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RejectFactCandidateCommandOutput>;
  rejectFactCandidate(
    args: RejectFactCandidateCommandInput,
    cb: (err: any, data?: RejectFactCandidateCommandOutput) => void
  ): void;
  rejectFactCandidate(
    args: RejectFactCandidateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RejectFactCandidateCommandOutput) => void
  ): void;

  /**
   * @see {@link UploadDocumentCommand}
   */
  uploadDocument(
    args: UploadDocumentCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UploadDocumentCommandOutput>;
  uploadDocument(
    args: UploadDocumentCommandInput,
    cb: (err: any, data?: UploadDocumentCommandOutput) => void
  ): void;
  uploadDocument(
    args: UploadDocumentCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UploadDocumentCommandOutput) => void
  ): void;

  /**
   * @see {@link GetEntityEmbeddingsCommand}
   */
  getEntityEmbeddings(
    args: GetEntityEmbeddingsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetEntityEmbeddingsCommandOutput>;
  getEntityEmbeddings(
    args: GetEntityEmbeddingsCommandInput,
    cb: (err: any, data?: GetEntityEmbeddingsCommandOutput) => void
  ): void;
  getEntityEmbeddings(
    args: GetEntityEmbeddingsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetEntityEmbeddingsCommandOutput) => void
  ): void;

  /**
   * @see {@link SearchEmbeddingsCommand}
   */
  searchEmbeddings(
    args: SearchEmbeddingsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SearchEmbeddingsCommandOutput>;
  searchEmbeddings(
    args: SearchEmbeddingsCommandInput,
    cb: (err: any, data?: SearchEmbeddingsCommandOutput) => void
  ): void;
  searchEmbeddings(
    args: SearchEmbeddingsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SearchEmbeddingsCommandOutput) => void
  ): void;

  /**
   * @see {@link CreateGrantCommand}
   */
  createGrant(
    args: CreateGrantCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateGrantCommandOutput>;
  createGrant(
    args: CreateGrantCommandInput,
    cb: (err: any, data?: CreateGrantCommandOutput) => void
  ): void;
  createGrant(
    args: CreateGrantCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateGrantCommandOutput) => void
  ): void;

  /**
   * @see {@link CreatePlatformGrantCommand}
   */
  createPlatformGrant(
    args: CreatePlatformGrantCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreatePlatformGrantCommandOutput>;
  createPlatformGrant(
    args: CreatePlatformGrantCommandInput,
    cb: (err: any, data?: CreatePlatformGrantCommandOutput) => void
  ): void;
  createPlatformGrant(
    args: CreatePlatformGrantCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreatePlatformGrantCommandOutput) => void
  ): void;

  /**
   * @see {@link DeleteGrantCommand}
   */
  deleteGrant(
    args: DeleteGrantCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteGrantCommandOutput>;
  deleteGrant(
    args: DeleteGrantCommandInput,
    cb: (err: any, data?: DeleteGrantCommandOutput) => void
  ): void;
  deleteGrant(
    args: DeleteGrantCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteGrantCommandOutput) => void
  ): void;

  /**
   * @see {@link DeletePlatformGrantCommand}
   */
  deletePlatformGrant(
    args: DeletePlatformGrantCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeletePlatformGrantCommandOutput>;
  deletePlatformGrant(
    args: DeletePlatformGrantCommandInput,
    cb: (err: any, data?: DeletePlatformGrantCommandOutput) => void
  ): void;
  deletePlatformGrant(
    args: DeletePlatformGrantCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeletePlatformGrantCommandOutput) => void
  ): void;

  /**
   * @see {@link ListNamespaceGrantsCommand}
   */
  listNamespaceGrants(
    args: ListNamespaceGrantsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListNamespaceGrantsCommandOutput>;
  listNamespaceGrants(
    args: ListNamespaceGrantsCommandInput,
    cb: (err: any, data?: ListNamespaceGrantsCommandOutput) => void
  ): void;
  listNamespaceGrants(
    args: ListNamespaceGrantsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListNamespaceGrantsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListPlatformGrantsCommand}
   */
  listPlatformGrants(): Promise<ListPlatformGrantsCommandOutput>;
  listPlatformGrants(
    args: ListPlatformGrantsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListPlatformGrantsCommandOutput>;
  listPlatformGrants(
    args: ListPlatformGrantsCommandInput,
    cb: (err: any, data?: ListPlatformGrantsCommandOutput) => void
  ): void;
  listPlatformGrants(
    args: ListPlatformGrantsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListPlatformGrantsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListPrincipalGrantsCommand}
   */
  listPrincipalGrants(
    args: ListPrincipalGrantsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListPrincipalGrantsCommandOutput>;
  listPrincipalGrants(
    args: ListPrincipalGrantsCommandInput,
    cb: (err: any, data?: ListPrincipalGrantsCommandOutput) => void
  ): void;
  listPrincipalGrants(
    args: ListPrincipalGrantsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListPrincipalGrantsCommandOutput) => void
  ): void;

  /**
   * @see {@link BulkDeleteMetricsCommand}
   */
  bulkDeleteMetrics(
    args: BulkDeleteMetricsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<BulkDeleteMetricsCommandOutput>;
  bulkDeleteMetrics(
    args: BulkDeleteMetricsCommandInput,
    cb: (err: any, data?: BulkDeleteMetricsCommandOutput) => void
  ): void;
  bulkDeleteMetrics(
    args: BulkDeleteMetricsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: BulkDeleteMetricsCommandOutput) => void
  ): void;

  /**
   * @see {@link CreateMetricCommand}
   */
  createMetric(
    args: CreateMetricCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateMetricCommandOutput>;
  createMetric(
    args: CreateMetricCommandInput,
    cb: (err: any, data?: CreateMetricCommandOutput) => void
  ): void;
  createMetric(
    args: CreateMetricCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateMetricCommandOutput) => void
  ): void;

  /**
   * @see {@link DeleteMetricCommand}
   */
  deleteMetric(
    args: DeleteMetricCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteMetricCommandOutput>;
  deleteMetric(
    args: DeleteMetricCommandInput,
    cb: (err: any, data?: DeleteMetricCommandOutput) => void
  ): void;
  deleteMetric(
    args: DeleteMetricCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteMetricCommandOutput) => void
  ): void;

  /**
   * @see {@link ExportOsiCommand}
   */
  exportOsi(
    args: ExportOsiCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ExportOsiCommandOutput>;
  exportOsi(
    args: ExportOsiCommandInput,
    cb: (err: any, data?: ExportOsiCommandOutput) => void
  ): void;
  exportOsi(
    args: ExportOsiCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ExportOsiCommandOutput) => void
  ): void;

  /**
   * @see {@link GetImportJobCommand}
   */
  getImportJob(
    args: GetImportJobCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetImportJobCommandOutput>;
  getImportJob(
    args: GetImportJobCommandInput,
    cb: (err: any, data?: GetImportJobCommandOutput) => void
  ): void;
  getImportJob(
    args: GetImportJobCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetImportJobCommandOutput) => void
  ): void;

  /**
   * @see {@link GetMetricCommand}
   */
  getMetric(
    args: GetMetricCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetMetricCommandOutput>;
  getMetric(
    args: GetMetricCommandInput,
    cb: (err: any, data?: GetMetricCommandOutput) => void
  ): void;
  getMetric(
    args: GetMetricCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetMetricCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOsiUploadUrlCommand}
   */
  getOsiUploadUrl(
    args: GetOsiUploadUrlCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOsiUploadUrlCommandOutput>;
  getOsiUploadUrl(
    args: GetOsiUploadUrlCommandInput,
    cb: (err: any, data?: GetOsiUploadUrlCommandOutput) => void
  ): void;
  getOsiUploadUrl(
    args: GetOsiUploadUrlCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOsiUploadUrlCommandOutput) => void
  ): void;

  /**
   * @see {@link ImportOsiCommand}
   */
  importOsi(
    args: ImportOsiCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ImportOsiCommandOutput>;
  importOsi(
    args: ImportOsiCommandInput,
    cb: (err: any, data?: ImportOsiCommandOutput) => void
  ): void;
  importOsi(
    args: ImportOsiCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ImportOsiCommandOutput) => void
  ): void;

  /**
   * @see {@link ListMetricsCommand}
   */
  listMetrics(
    args: ListMetricsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListMetricsCommandOutput>;
  listMetrics(
    args: ListMetricsCommandInput,
    cb: (err: any, data?: ListMetricsCommandOutput) => void
  ): void;
  listMetrics(
    args: ListMetricsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListMetricsCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateMetricCommand}
   */
  updateMetric(
    args: UpdateMetricCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateMetricCommandOutput>;
  updateMetric(
    args: UpdateMetricCommandInput,
    cb: (err: any, data?: UpdateMetricCommandOutput) => void
  ): void;
  updateMetric(
    args: UpdateMetricCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateMetricCommandOutput) => void
  ): void;

  /**
   * @see {@link ValidateMetricCommand}
   */
  validateMetric(
    args: ValidateMetricCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ValidateMetricCommandOutput>;
  validateMetric(
    args: ValidateMetricCommandInput,
    cb: (err: any, data?: ValidateMetricCommandOutput) => void
  ): void;
  validateMetric(
    args: ValidateMetricCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ValidateMetricCommandOutput) => void
  ): void;

  /**
   * @see {@link CreateNamespaceCommand}
   */
  createNamespace(
    args: CreateNamespaceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateNamespaceCommandOutput>;
  createNamespace(
    args: CreateNamespaceCommandInput,
    cb: (err: any, data?: CreateNamespaceCommandOutput) => void
  ): void;
  createNamespace(
    args: CreateNamespaceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateNamespaceCommandOutput) => void
  ): void;

  /**
   * @see {@link DeleteNamespaceCommand}
   */
  deleteNamespace(
    args: DeleteNamespaceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteNamespaceCommandOutput>;
  deleteNamespace(
    args: DeleteNamespaceCommandInput,
    cb: (err: any, data?: DeleteNamespaceCommandOutput) => void
  ): void;
  deleteNamespace(
    args: DeleteNamespaceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteNamespaceCommandOutput) => void
  ): void;

  /**
   * @see {@link GetNamespaceCommand}
   */
  getNamespace(
    args: GetNamespaceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetNamespaceCommandOutput>;
  getNamespace(
    args: GetNamespaceCommandInput,
    cb: (err: any, data?: GetNamespaceCommandOutput) => void
  ): void;
  getNamespace(
    args: GetNamespaceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetNamespaceCommandOutput) => void
  ): void;

  /**
   * @see {@link ListNamespacesCommand}
   */
  listNamespaces(): Promise<ListNamespacesCommandOutput>;
  listNamespaces(
    args: ListNamespacesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListNamespacesCommandOutput>;
  listNamespaces(
    args: ListNamespacesCommandInput,
    cb: (err: any, data?: ListNamespacesCommandOutput) => void
  ): void;
  listNamespaces(
    args: ListNamespacesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListNamespacesCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateNamespaceCommand}
   */
  updateNamespace(
    args: UpdateNamespaceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateNamespaceCommandOutput>;
  updateNamespace(
    args: UpdateNamespaceCommandInput,
    cb: (err: any, data?: UpdateNamespaceCommandOutput) => void
  ): void;
  updateNamespace(
    args: UpdateNamespaceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateNamespaceCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateNamespaceStatusCommand}
   */
  updateNamespaceStatus(
    args: UpdateNamespaceStatusCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateNamespaceStatusCommandOutput>;
  updateNamespaceStatus(
    args: UpdateNamespaceStatusCommandInput,
    cb: (err: any, data?: UpdateNamespaceStatusCommandOutput) => void
  ): void;
  updateNamespaceStatus(
    args: UpdateNamespaceStatusCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateNamespaceStatusCommandOutput) => void
  ): void;

  /**
   * @see {@link DeleteOntologyCommand}
   */
  deleteOntology(
    args: DeleteOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteOntologyCommandOutput>;
  deleteOntology(
    args: DeleteOntologyCommandInput,
    cb: (err: any, data?: DeleteOntologyCommandOutput) => void
  ): void;
  deleteOntology(
    args: DeleteOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link DownloadOntologyCommand}
   */
  downloadOntology(
    args: DownloadOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DownloadOntologyCommandOutput>;
  downloadOntology(
    args: DownloadOntologyCommandInput,
    cb: (err: any, data?: DownloadOntologyCommandOutput) => void
  ): void;
  downloadOntology(
    args: DownloadOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DownloadOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link FetchOntologyCommand}
   */
  fetchOntology(
    args: FetchOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<FetchOntologyCommandOutput>;
  fetchOntology(
    args: FetchOntologyCommandInput,
    cb: (err: any, data?: FetchOntologyCommandOutput) => void
  ): void;
  fetchOntology(
    args: FetchOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: FetchOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link GetCanvasManifestCommand}
   */
  getCanvasManifest(
    args: GetCanvasManifestCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetCanvasManifestCommandOutput>;
  getCanvasManifest(
    args: GetCanvasManifestCommandInput,
    cb: (err: any, data?: GetCanvasManifestCommandOutput) => void
  ): void;
  getCanvasManifest(
    args: GetCanvasManifestCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetCanvasManifestCommandOutput) => void
  ): void;

  /**
   * @see {@link GetGraphClassCommand}
   */
  getGraphClass(
    args: GetGraphClassCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetGraphClassCommandOutput>;
  getGraphClass(
    args: GetGraphClassCommandInput,
    cb: (err: any, data?: GetGraphClassCommandOutput) => void
  ): void;
  getGraphClass(
    args: GetGraphClassCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetGraphClassCommandOutput) => void
  ): void;

  /**
   * @see {@link GetGraphDatatypePropertyCommand}
   */
  getGraphDatatypeProperty(
    args: GetGraphDatatypePropertyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetGraphDatatypePropertyCommandOutput>;
  getGraphDatatypeProperty(
    args: GetGraphDatatypePropertyCommandInput,
    cb: (err: any, data?: GetGraphDatatypePropertyCommandOutput) => void
  ): void;
  getGraphDatatypeProperty(
    args: GetGraphDatatypePropertyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetGraphDatatypePropertyCommandOutput) => void
  ): void;

  /**
   * @see {@link GetGraphObjectPropertyCommand}
   */
  getGraphObjectProperty(
    args: GetGraphObjectPropertyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetGraphObjectPropertyCommandOutput>;
  getGraphObjectProperty(
    args: GetGraphObjectPropertyCommandInput,
    cb: (err: any, data?: GetGraphObjectPropertyCommandOutput) => void
  ): void;
  getGraphObjectProperty(
    args: GetGraphObjectPropertyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetGraphObjectPropertyCommandOutput) => void
  ): void;

  /**
   * @see {@link GetIngestStatusCommand}
   */
  getIngestStatus(
    args: GetIngestStatusCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetIngestStatusCommandOutput>;
  getIngestStatus(
    args: GetIngestStatusCommandInput,
    cb: (err: any, data?: GetIngestStatusCommandOutput) => void
  ): void;
  getIngestStatus(
    args: GetIngestStatusCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetIngestStatusCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOntologyCommand}
   */
  getOntology(
    args: GetOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyCommandOutput>;
  getOntology(
    args: GetOntologyCommandInput,
    cb: (err: any, data?: GetOntologyCommandOutput) => void
  ): void;
  getOntology(
    args: GetOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOntologyOverviewCommand}
   */
  getOntologyOverview(
    args: GetOntologyOverviewCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyOverviewCommandOutput>;
  getOntologyOverview(
    args: GetOntologyOverviewCommandInput,
    cb: (err: any, data?: GetOntologyOverviewCommandOutput) => void
  ): void;
  getOntologyOverview(
    args: GetOntologyOverviewCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyOverviewCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOntologyUploadUrlCommand}
   */
  getOntologyUploadUrl(
    args: GetOntologyUploadUrlCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyUploadUrlCommandOutput>;
  getOntologyUploadUrl(
    args: GetOntologyUploadUrlCommandInput,
    cb: (err: any, data?: GetOntologyUploadUrlCommandOutput) => void
  ): void;
  getOntologyUploadUrl(
    args: GetOntologyUploadUrlCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyUploadUrlCommandOutput) => void
  ): void;

  /**
   * @see {@link GraphSearchCommand}
   */
  graphSearch(
    args: GraphSearchCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GraphSearchCommandOutput>;
  graphSearch(
    args: GraphSearchCommandInput,
    cb: (err: any, data?: GraphSearchCommandOutput) => void
  ): void;
  graphSearch(
    args: GraphSearchCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GraphSearchCommandOutput) => void
  ): void;

  /**
   * @see {@link IngestOntologyFromS3Command}
   */
  ingestOntologyFromS3(
    args: IngestOntologyFromS3CommandInput,
    options?: __HttpHandlerOptions
  ): Promise<IngestOntologyFromS3CommandOutput>;
  ingestOntologyFromS3(
    args: IngestOntologyFromS3CommandInput,
    cb: (err: any, data?: IngestOntologyFromS3CommandOutput) => void
  ): void;
  ingestOntologyFromS3(
    args: IngestOntologyFromS3CommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: IngestOntologyFromS3CommandOutput) => void
  ): void;

  /**
   * @see {@link ListOntologiesCommand}
   */
  listOntologies(
    args: ListOntologiesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListOntologiesCommandOutput>;
  listOntologies(
    args: ListOntologiesCommandInput,
    cb: (err: any, data?: ListOntologiesCommandOutput) => void
  ): void;
  listOntologies(
    args: ListOntologiesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListOntologiesCommandOutput) => void
  ): void;

  /**
   * @see {@link ListStatementsCommand}
   */
  listStatements(
    args: ListStatementsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListStatementsCommandOutput>;
  listStatements(
    args: ListStatementsCommandInput,
    cb: (err: any, data?: ListStatementsCommandOutput) => void
  ): void;
  listStatements(
    args: ListStatementsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListStatementsCommandOutput) => void
  ): void;

  /**
   * @see {@link UploadOntologyCommand}
   */
  uploadOntology(
    args: UploadOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UploadOntologyCommandOutput>;
  uploadOntology(
    args: UploadOntologyCommandInput,
    cb: (err: any, data?: UploadOntologyCommandOutput) => void
  ): void;
  uploadOntology(
    args: UploadOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UploadOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link AcceptProposalCommand}
   */
  acceptProposal(
    args: AcceptProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<AcceptProposalCommandOutput>;
  acceptProposal(
    args: AcceptProposalCommandInput,
    cb: (err: any, data?: AcceptProposalCommandOutput) => void
  ): void;
  acceptProposal(
    args: AcceptProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: AcceptProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link CancelProposalCommand}
   */
  cancelProposal(
    args: CancelProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CancelProposalCommandOutput>;
  cancelProposal(
    args: CancelProposalCommandInput,
    cb: (err: any, data?: CancelProposalCommandOutput) => void
  ): void;
  cancelProposal(
    args: CancelProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CancelProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link CompileConstraintsCommand}
   */
  compileConstraints(
    args: CompileConstraintsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CompileConstraintsCommandOutput>;
  compileConstraints(
    args: CompileConstraintsCommandInput,
    cb: (err: any, data?: CompileConstraintsCommandOutput) => void
  ): void;
  compileConstraints(
    args: CompileConstraintsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CompileConstraintsCommandOutput) => void
  ): void;

  /**
   * @see {@link GetInductionJobCommand}
   */
  getInductionJob(
    args: GetInductionJobCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetInductionJobCommandOutput>;
  getInductionJob(
    args: GetInductionJobCommandInput,
    cb: (err: any, data?: GetInductionJobCommandOutput) => void
  ): void;
  getInductionJob(
    args: GetInductionJobCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetInductionJobCommandOutput) => void
  ): void;

  /**
   * @see {@link GetInferConstraintsJobCommand}
   */
  getInferConstraintsJob(
    args: GetInferConstraintsJobCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetInferConstraintsJobCommandOutput>;
  getInferConstraintsJob(
    args: GetInferConstraintsJobCommandInput,
    cb: (err: any, data?: GetInferConstraintsJobCommandOutput) => void
  ): void;
  getInferConstraintsJob(
    args: GetInferConstraintsJobCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetInferConstraintsJobCommandOutput) => void
  ): void;

  /**
   * @see {@link GetProposalCommand}
   */
  getProposal(
    args: GetProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetProposalCommandOutput>;
  getProposal(
    args: GetProposalCommandInput,
    cb: (err: any, data?: GetProposalCommandOutput) => void
  ): void;
  getProposal(
    args: GetProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link GetProposalUploadUrlsCommand}
   */
  getProposalUploadUrls(
    args: GetProposalUploadUrlsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetProposalUploadUrlsCommandOutput>;
  getProposalUploadUrls(
    args: GetProposalUploadUrlsCommandInput,
    cb: (err: any, data?: GetProposalUploadUrlsCommandOutput) => void
  ): void;
  getProposalUploadUrls(
    args: GetProposalUploadUrlsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetProposalUploadUrlsCommandOutput) => void
  ): void;

  /**
   * @see {@link GetProposalValidationJobCommand}
   */
  getProposalValidationJob(
    args: GetProposalValidationJobCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetProposalValidationJobCommandOutput>;
  getProposalValidationJob(
    args: GetProposalValidationJobCommandInput,
    cb: (err: any, data?: GetProposalValidationJobCommandOutput) => void
  ): void;
  getProposalValidationJob(
    args: GetProposalValidationJobCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetProposalValidationJobCommandOutput) => void
  ): void;

  /**
   * @see {@link InferConstraintsCommand}
   */
  inferConstraints(
    args: InferConstraintsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<InferConstraintsCommandOutput>;
  inferConstraints(
    args: InferConstraintsCommandInput,
    cb: (err: any, data?: InferConstraintsCommandOutput) => void
  ): void;
  inferConstraints(
    args: InferConstraintsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: InferConstraintsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListFoundationalOntologiesCommand}
   */
  listFoundationalOntologies(
    args: ListFoundationalOntologiesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListFoundationalOntologiesCommandOutput>;
  listFoundationalOntologies(
    args: ListFoundationalOntologiesCommandInput,
    cb: (err: any, data?: ListFoundationalOntologiesCommandOutput) => void
  ): void;
  listFoundationalOntologies(
    args: ListFoundationalOntologiesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListFoundationalOntologiesCommandOutput) => void
  ): void;

  /**
   * @see {@link ListInducedDatasourcesCommand}
   */
  listInducedDatasources(
    args: ListInducedDatasourcesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListInducedDatasourcesCommandOutput>;
  listInducedDatasources(
    args: ListInducedDatasourcesCommandInput,
    cb: (err: any, data?: ListInducedDatasourcesCommandOutput) => void
  ): void;
  listInducedDatasources(
    args: ListInducedDatasourcesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListInducedDatasourcesCommandOutput) => void
  ): void;

  /**
   * @see {@link ListInductionJobsCommand}
   */
  listInductionJobs(
    args: ListInductionJobsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListInductionJobsCommandOutput>;
  listInductionJobs(
    args: ListInductionJobsCommandInput,
    cb: (err: any, data?: ListInductionJobsCommandOutput) => void
  ): void;
  listInductionJobs(
    args: ListInductionJobsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListInductionJobsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListProposalsCommand}
   */
  listProposals(
    args: ListProposalsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListProposalsCommandOutput>;
  listProposals(
    args: ListProposalsCommandInput,
    cb: (err: any, data?: ListProposalsCommandOutput) => void
  ): void;
  listProposals(
    args: ListProposalsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListProposalsCommandOutput) => void
  ): void;

  /**
   * @see {@link LoadFoundationalOntologyCommand}
   */
  loadFoundationalOntology(
    args: LoadFoundationalOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<LoadFoundationalOntologyCommandOutput>;
  loadFoundationalOntology(
    args: LoadFoundationalOntologyCommandInput,
    cb: (err: any, data?: LoadFoundationalOntologyCommandOutput) => void
  ): void;
  loadFoundationalOntology(
    args: LoadFoundationalOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: LoadFoundationalOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link RejectProposalsCommand}
   */
  rejectProposals(
    args: RejectProposalsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RejectProposalsCommandOutput>;
  rejectProposals(
    args: RejectProposalsCommandInput,
    cb: (err: any, data?: RejectProposalsCommandOutput) => void
  ): void;
  rejectProposals(
    args: RejectProposalsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RejectProposalsCommandOutput) => void
  ): void;

  /**
   * @see {@link RepairProposalDatatypesCommand}
   */
  repairProposalDatatypes(
    args: RepairProposalDatatypesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RepairProposalDatatypesCommandOutput>;
  repairProposalDatatypes(
    args: RepairProposalDatatypesCommandInput,
    cb: (err: any, data?: RepairProposalDatatypesCommandOutput) => void
  ): void;
  repairProposalDatatypes(
    args: RepairProposalDatatypesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RepairProposalDatatypesCommandOutput) => void
  ): void;

  /**
   * @see {@link StartInductionCommand}
   */
  startInduction(
    args: StartInductionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<StartInductionCommandOutput>;
  startInduction(
    args: StartInductionCommandInput,
    cb: (err: any, data?: StartInductionCommandOutput) => void
  ): void;
  startInduction(
    args: StartInductionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: StartInductionCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateProposalCommand}
   */
  updateProposal(
    args: UpdateProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateProposalCommandOutput>;
  updateProposal(
    args: UpdateProposalCommandInput,
    cb: (err: any, data?: UpdateProposalCommandOutput) => void
  ): void;
  updateProposal(
    args: UpdateProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link ValidateProposalCommand}
   */
  validateProposal(
    args: ValidateProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ValidateProposalCommandOutput>;
  validateProposal(
    args: ValidateProposalCommandInput,
    cb: (err: any, data?: ValidateProposalCommandOutput) => void
  ): void;
  validateProposal(
    args: ValidateProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ValidateProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link GetNamespaceRoleCommand}
   */
  getNamespaceRole(
    args: GetNamespaceRoleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetNamespaceRoleCommandOutput>;
  getNamespaceRole(
    args: GetNamespaceRoleCommandInput,
    cb: (err: any, data?: GetNamespaceRoleCommandOutput) => void
  ): void;
  getNamespaceRole(
    args: GetNamespaceRoleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetNamespaceRoleCommandOutput) => void
  ): void;

  /**
   * @see {@link ListNamespaceRolesCommand}
   */
  listNamespaceRoles(
    args: ListNamespaceRolesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListNamespaceRolesCommandOutput>;
  listNamespaceRoles(
    args: ListNamespaceRolesCommandInput,
    cb: (err: any, data?: ListNamespaceRolesCommandOutput) => void
  ): void;
  listNamespaceRoles(
    args: ListNamespaceRolesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListNamespaceRolesCommandOutput) => void
  ): void;

  /**
   * @see {@link ListPlatformRolesCommand}
   */
  listPlatformRoles(): Promise<ListPlatformRolesCommandOutput>;
  listPlatformRoles(
    args: ListPlatformRolesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListPlatformRolesCommandOutput>;
  listPlatformRoles(
    args: ListPlatformRolesCommandInput,
    cb: (err: any, data?: ListPlatformRolesCommandOutput) => void
  ): void;
  listPlatformRoles(
    args: ListPlatformRolesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListPlatformRolesCommandOutput) => void
  ): void;

  /**
   * @see {@link ApproveSourceCommand}
   */
  approveSource(
    args: ApproveSourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ApproveSourceCommandOutput>;
  approveSource(
    args: ApproveSourceCommandInput,
    cb: (err: any, data?: ApproveSourceCommandOutput) => void
  ): void;
  approveSource(
    args: ApproveSourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ApproveSourceCommandOutput) => void
  ): void;

  /**
   * @see {@link CreateSourceCommand}
   */
  createSource(
    args: CreateSourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateSourceCommandOutput>;
  createSource(
    args: CreateSourceCommandInput,
    cb: (err: any, data?: CreateSourceCommandOutput) => void
  ): void;
  createSource(
    args: CreateSourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateSourceCommandOutput) => void
  ): void;

  /**
   * @see {@link DeleteSourceCommand}
   */
  deleteSource(
    args: DeleteSourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteSourceCommandOutput>;
  deleteSource(
    args: DeleteSourceCommandInput,
    cb: (err: any, data?: DeleteSourceCommandOutput) => void
  ): void;
  deleteSource(
    args: DeleteSourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteSourceCommandOutput) => void
  ): void;

  /**
   * @see {@link GetSourceCommand}
   */
  getSource(
    args: GetSourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSourceCommandOutput>;
  getSource(
    args: GetSourceCommandInput,
    cb: (err: any, data?: GetSourceCommandOutput) => void
  ): void;
  getSource(
    args: GetSourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSourceCommandOutput) => void
  ): void;

  /**
   * @see {@link GetSourceScanJobCommand}
   */
  getSourceScanJob(
    args: GetSourceScanJobCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSourceScanJobCommandOutput>;
  getSourceScanJob(
    args: GetSourceScanJobCommandInput,
    cb: (err: any, data?: GetSourceScanJobCommandOutput) => void
  ): void;
  getSourceScanJob(
    args: GetSourceScanJobCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSourceScanJobCommandOutput) => void
  ): void;

  /**
   * @see {@link GetSourceTableCommand}
   */
  getSourceTable(
    args: GetSourceTableCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSourceTableCommandOutput>;
  getSourceTable(
    args: GetSourceTableCommandInput,
    cb: (err: any, data?: GetSourceTableCommandOutput) => void
  ): void;
  getSourceTable(
    args: GetSourceTableCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSourceTableCommandOutput) => void
  ): void;

  /**
   * @see {@link GetSourceUploadUrlsCommand}
   */
  getSourceUploadUrls(
    args: GetSourceUploadUrlsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetSourceUploadUrlsCommandOutput>;
  getSourceUploadUrls(
    args: GetSourceUploadUrlsCommandInput,
    cb: (err: any, data?: GetSourceUploadUrlsCommandOutput) => void
  ): void;
  getSourceUploadUrls(
    args: GetSourceUploadUrlsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetSourceUploadUrlsCommandOutput) => void
  ): void;

  /**
   * @see {@link KeepRescanRemovalCommand}
   */
  keepRescanRemoval(
    args: KeepRescanRemovalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<KeepRescanRemovalCommandOutput>;
  keepRescanRemoval(
    args: KeepRescanRemovalCommandInput,
    cb: (err: any, data?: KeepRescanRemovalCommandOutput) => void
  ): void;
  keepRescanRemoval(
    args: KeepRescanRemovalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: KeepRescanRemovalCommandOutput) => void
  ): void;

  /**
   * @see {@link ListSourcesCommand}
   */
  listSources(
    args: ListSourcesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListSourcesCommandOutput>;
  listSources(
    args: ListSourcesCommandInput,
    cb: (err: any, data?: ListSourcesCommandOutput) => void
  ): void;
  listSources(
    args: ListSourcesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListSourcesCommandOutput) => void
  ): void;

  /**
   * @see {@link ListSourceScanJobsCommand}
   */
  listSourceScanJobs(
    args: ListSourceScanJobsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListSourceScanJobsCommandOutput>;
  listSourceScanJobs(
    args: ListSourceScanJobsCommandInput,
    cb: (err: any, data?: ListSourceScanJobsCommandOutput) => void
  ): void;
  listSourceScanJobs(
    args: ListSourceScanJobsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListSourceScanJobsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListSourceTablesCommand}
   */
  listSourceTables(
    args: ListSourceTablesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListSourceTablesCommandOutput>;
  listSourceTables(
    args: ListSourceTablesCommandInput,
    cb: (err: any, data?: ListSourceTablesCommandOutput) => void
  ): void;
  listSourceTables(
    args: ListSourceTablesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListSourceTablesCommandOutput) => void
  ): void;

  /**
   * @see {@link PutSourceEventRescanCommand}
   */
  putSourceEventRescan(
    args: PutSourceEventRescanCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<PutSourceEventRescanCommandOutput>;
  putSourceEventRescan(
    args: PutSourceEventRescanCommandInput,
    cb: (err: any, data?: PutSourceEventRescanCommandOutput) => void
  ): void;
  putSourceEventRescan(
    args: PutSourceEventRescanCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: PutSourceEventRescanCommandOutput) => void
  ): void;

  /**
   * @see {@link PutSourceRescanScheduleCommand}
   */
  putSourceRescanSchedule(
    args: PutSourceRescanScheduleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<PutSourceRescanScheduleCommandOutput>;
  putSourceRescanSchedule(
    args: PutSourceRescanScheduleCommandInput,
    cb: (err: any, data?: PutSourceRescanScheduleCommandOutput) => void
  ): void;
  putSourceRescanSchedule(
    args: PutSourceRescanScheduleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: PutSourceRescanScheduleCommandOutput) => void
  ): void;

  /**
   * @see {@link RejectSourceCommand}
   */
  rejectSource(
    args: RejectSourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RejectSourceCommandOutput>;
  rejectSource(
    args: RejectSourceCommandInput,
    cb: (err: any, data?: RejectSourceCommandOutput) => void
  ): void;
  rejectSource(
    args: RejectSourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RejectSourceCommandOutput) => void
  ): void;

  /**
   * @see {@link RescanSourceCommand}
   */
  rescanSource(
    args: RescanSourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RescanSourceCommandOutput>;
  rescanSource(
    args: RescanSourceCommandInput,
    cb: (err: any, data?: RescanSourceCommandOutput) => void
  ): void;
  rescanSource(
    args: RescanSourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RescanSourceCommandOutput) => void
  ): void;

  /**
   * @see {@link ReviewSourceColumnCommand}
   */
  reviewSourceColumn(
    args: ReviewSourceColumnCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ReviewSourceColumnCommandOutput>;
  reviewSourceColumn(
    args: ReviewSourceColumnCommandInput,
    cb: (err: any, data?: ReviewSourceColumnCommandOutput) => void
  ): void;
  reviewSourceColumn(
    args: ReviewSourceColumnCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ReviewSourceColumnCommandOutput) => void
  ): void;

  /**
   * @see {@link ReviewSourceTableCommand}
   */
  reviewSourceTable(
    args: ReviewSourceTableCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ReviewSourceTableCommandOutput>;
  reviewSourceTable(
    args: ReviewSourceTableCommandInput,
    cb: (err: any, data?: ReviewSourceTableCommandOutput) => void
  ): void;
  reviewSourceTable(
    args: ReviewSourceTableCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ReviewSourceTableCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateSourceColumnMetadataCommand}
   */
  updateSourceColumnMetadata(
    args: UpdateSourceColumnMetadataCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateSourceColumnMetadataCommandOutput>;
  updateSourceColumnMetadata(
    args: UpdateSourceColumnMetadataCommandInput,
    cb: (err: any, data?: UpdateSourceColumnMetadataCommandOutput) => void
  ): void;
  updateSourceColumnMetadata(
    args: UpdateSourceColumnMetadataCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateSourceColumnMetadataCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateSourceMetadataCommand}
   */
  updateSourceMetadata(
    args: UpdateSourceMetadataCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateSourceMetadataCommandOutput>;
  updateSourceMetadata(
    args: UpdateSourceMetadataCommandInput,
    cb: (err: any, data?: UpdateSourceMetadataCommandOutput) => void
  ): void;
  updateSourceMetadata(
    args: UpdateSourceMetadataCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateSourceMetadataCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateSourceTableKeysCommand}
   */
  updateSourceTableKeys(
    args: UpdateSourceTableKeysCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateSourceTableKeysCommandOutput>;
  updateSourceTableKeys(
    args: UpdateSourceTableKeysCommandInput,
    cb: (err: any, data?: UpdateSourceTableKeysCommandOutput) => void
  ): void;
  updateSourceTableKeys(
    args: UpdateSourceTableKeysCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateSourceTableKeysCommandOutput) => void
  ): void;

  /**
   * @see {@link UpdateSourceTableMetadataCommand}
   */
  updateSourceTableMetadata(
    args: UpdateSourceTableMetadataCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateSourceTableMetadataCommandOutput>;
  updateSourceTableMetadata(
    args: UpdateSourceTableMetadataCommandInput,
    cb: (err: any, data?: UpdateSourceTableMetadataCommandOutput) => void
  ): void;
  updateSourceTableMetadata(
    args: UpdateSourceTableMetadataCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateSourceTableMetadataCommandOutput) => void
  ): void;

  /**
   * @see {@link ListDocumentChunksCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListDocumentChunksCommandOutput}.
   */
  paginateListDocumentChunks(
    args: ListDocumentChunksCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListDocumentChunksCommandOutput>;

  /**
   * @see {@link ListDocumentsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListDocumentsCommandOutput}.
   */
  paginateListDocuments(
    args: ListDocumentsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListDocumentsCommandOutput>;

  /**
   * @see {@link ListFactCandidatesCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListFactCandidatesCommandOutput}.
   */
  paginateListFactCandidates(
    args: ListFactCandidatesCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListFactCandidatesCommandOutput>;

  /**
   * @see {@link ListNamespaceGrantsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListNamespaceGrantsCommandOutput}.
   */
  paginateListNamespaceGrants(
    args: ListNamespaceGrantsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListNamespaceGrantsCommandOutput>;

  /**
   * @see {@link ListPlatformGrantsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListPlatformGrantsCommandOutput}.
   */
  paginateListPlatformGrants(
    args?: ListPlatformGrantsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListPlatformGrantsCommandOutput>;

  /**
   * @see {@link ListPrincipalGrantsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListPrincipalGrantsCommandOutput}.
   */
  paginateListPrincipalGrants(
    args: ListPrincipalGrantsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListPrincipalGrantsCommandOutput>;

  /**
   * @see {@link ListMetricsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListMetricsCommandOutput}.
   */
  paginateListMetrics(
    args: ListMetricsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListMetricsCommandOutput>;

  /**
   * @see {@link ListNamespacesCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListNamespacesCommandOutput}.
   */
  paginateListNamespaces(
    args?: ListNamespacesCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListNamespacesCommandOutput>;

  /**
   * @see {@link ListOntologiesCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListOntologiesCommandOutput}.
   */
  paginateListOntologies(
    args: ListOntologiesCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListOntologiesCommandOutput>;

  /**
   * @see {@link ListInducedDatasourcesCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListInducedDatasourcesCommandOutput}.
   */
  paginateListInducedDatasources(
    args: ListInducedDatasourcesCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListInducedDatasourcesCommandOutput>;

  /**
   * @see {@link ListInductionJobsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListInductionJobsCommandOutput}.
   */
  paginateListInductionJobs(
    args: ListInductionJobsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListInductionJobsCommandOutput>;

  /**
   * @see {@link ListProposalsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListProposalsCommandOutput}.
   */
  paginateListProposals(
    args: ListProposalsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListProposalsCommandOutput>;

  /**
   * @see {@link ListSourcesCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListSourcesCommandOutput}.
   */
  paginateListSources(
    args: ListSourcesCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListSourcesCommandOutput>;

  /**
   * @see {@link ListSourceScanJobsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListSourceScanJobsCommandOutput}.
   */
  paginateListSourceScanJobs(
    args: ListSourceScanJobsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListSourceScanJobsCommandOutput>;

  /**
   * @see {@link ListSourceTablesCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListSourceTablesCommandOutput}.
   */
  paginateListSourceTables(
    args: ListSourceTablesCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListSourceTablesCommandOutput>;
}

/**
 * @public
 */
export class ControlPlaneService extends ControlPlaneServiceClient implements ControlPlaneService {}
createAggregatedClient(commands, ControlPlaneService, { paginators });
