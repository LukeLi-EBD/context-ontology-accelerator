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
  type AssertFactCommandInput,
  type AssertFactCommandOutput,
  AssertFactCommand,
} from "./commands/AssertFactCommand";
import {
  type BatchKeepFactConflictsCommandInput,
  type BatchKeepFactConflictsCommandOutput,
  BatchKeepFactConflictsCommand,
} from "./commands/BatchKeepFactConflictsCommand";
import {
  type BrowseOntologyTreeCommandInput,
  type BrowseOntologyTreeCommandOutput,
  BrowseOntologyTreeCommand,
} from "./commands/BrowseOntologyTreeCommand";
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
  type DiffOntologyVersionsCommandInput,
  type DiffOntologyVersionsCommandOutput,
  DiffOntologyVersionsCommand,
} from "./commands/DiffOntologyVersionsCommand";
import {
  type DownloadOntologyCommandInput,
  type DownloadOntologyCommandOutput,
  DownloadOntologyCommand,
} from "./commands/DownloadOntologyCommand";
import {
  type ExportOntologyBundleCommandInput,
  type ExportOntologyBundleCommandOutput,
  ExportOntologyBundleCommand,
} from "./commands/ExportOntologyBundleCommand";
import {
  type ExportOntologyVersionCommandInput,
  type ExportOntologyVersionCommandOutput,
  ExportOntologyVersionCommand,
} from "./commands/ExportOntologyVersionCommand";
import { type ExportOsiCommandInput, type ExportOsiCommandOutput, ExportOsiCommand } from "./commands/ExportOsiCommand";
import {
  type FetchOntologyCommandInput,
  type FetchOntologyCommandOutput,
  FetchOntologyCommand,
} from "./commands/FetchOntologyCommand";
import {
  type FindGraphPathCommandInput,
  type FindGraphPathCommandOutput,
  FindGraphPathCommand,
} from "./commands/FindGraphPathCommand";
import { type FindLinksCommandInput, type FindLinksCommandOutput, FindLinksCommand } from "./commands/FindLinksCommand";
import {
  type GetAnswerQualityCommandInput,
  type GetAnswerQualityCommandOutput,
  GetAnswerQualityCommand,
} from "./commands/GetAnswerQualityCommand";
import {
  type GetCanvasManifestCommandInput,
  type GetCanvasManifestCommandOutput,
  GetCanvasManifestCommand,
} from "./commands/GetCanvasManifestCommand";
import {
  type GetCanvasSubgraphCommandInput,
  type GetCanvasSubgraphCommandOutput,
  GetCanvasSubgraphCommand,
} from "./commands/GetCanvasSubgraphCommand";
import {
  type GetDictionaryCommandInput,
  type GetDictionaryCommandOutput,
  GetDictionaryCommand,
} from "./commands/GetDictionaryCommand";
import {
  type GetDictionaryCommentCoverageCommandInput,
  type GetDictionaryCommentCoverageCommandOutput,
  GetDictionaryCommentCoverageCommand,
} from "./commands/GetDictionaryCommentCoverageCommand";
import {
  type GetDictionaryViewCommandInput,
  type GetDictionaryViewCommandOutput,
  GetDictionaryViewCommand,
} from "./commands/GetDictionaryViewCommand";
import { type GetEntityCommandInput, type GetEntityCommandOutput, GetEntityCommand } from "./commands/GetEntityCommand";
import {
  type GetEntityEmbeddingsCommandInput,
  type GetEntityEmbeddingsCommandOutput,
  GetEntityEmbeddingsCommand,
} from "./commands/GetEntityEmbeddingsCommand";
import {
  type GetEntityProvenanceCommandInput,
  type GetEntityProvenanceCommandOutput,
  GetEntityProvenanceCommand,
} from "./commands/GetEntityProvenanceCommand";
import { type GetFactCommandInput, type GetFactCommandOutput, GetFactCommand } from "./commands/GetFactCommand";
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
import {
  type GetMetricCardCommandInput,
  type GetMetricCardCommandOutput,
  GetMetricCardCommand,
} from "./commands/GetMetricCardCommand";
import { type GetMetricCommandInput, type GetMetricCommandOutput, GetMetricCommand } from "./commands/GetMetricCommand";
import {
  type GetMetricFamilyCommandInput,
  type GetMetricFamilyCommandOutput,
  GetMetricFamilyCommand,
} from "./commands/GetMetricFamilyCommand";
import {
  type GetMetricReportManifestCommandInput,
  type GetMetricReportManifestCommandOutput,
  GetMetricReportManifestCommand,
} from "./commands/GetMetricReportManifestCommand";
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
  type GetOntologyDiffCommandInput,
  type GetOntologyDiffCommandOutput,
  GetOntologyDiffCommand,
} from "./commands/GetOntologyDiffCommand";
import {
  type GetOntologyOverviewCommandInput,
  type GetOntologyOverviewCommandOutput,
  GetOntologyOverviewCommand,
} from "./commands/GetOntologyOverviewCommand";
import {
  type GetOntologySnapshotCommandInput,
  type GetOntologySnapshotCommandOutput,
  GetOntologySnapshotCommand,
} from "./commands/GetOntologySnapshotCommand";
import {
  type GetOntologyUploadUrlCommandInput,
  type GetOntologyUploadUrlCommandOutput,
  GetOntologyUploadUrlCommand,
} from "./commands/GetOntologyUploadUrlCommand";
import {
  type GetOntologyValidationJobCommandInput,
  type GetOntologyValidationJobCommandOutput,
  GetOntologyValidationJobCommand,
} from "./commands/GetOntologyValidationJobCommand";
import {
  type GetOntologyVersionCommandInput,
  type GetOntologyVersionCommandOutput,
  GetOntologyVersionCommand,
} from "./commands/GetOntologyVersionCommand";
import {
  type GetOntologyVersionProposalCommandInput,
  type GetOntologyVersionProposalCommandOutput,
  GetOntologyVersionProposalCommand,
} from "./commands/GetOntologyVersionProposalCommand";
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
import {
  type GetReasoningStatusCommandInput,
  type GetReasoningStatusCommandOutput,
  GetReasoningStatusCommand,
} from "./commands/GetReasoningStatusCommand";
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
import {
  type ImportBundleCommandInput,
  type ImportBundleCommandOutput,
  ImportBundleCommand,
} from "./commands/ImportBundleCommand";
import {
  type ImportOntologyCommandInput,
  type ImportOntologyCommandOutput,
  ImportOntologyCommand,
} from "./commands/ImportOntologyCommand";
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
  type InspectOntologyBundleCommandInput,
  type InspectOntologyBundleCommandOutput,
  InspectOntologyBundleCommand,
} from "./commands/InspectOntologyBundleCommand";
import {
  type KeepRescanRemovalCommandInput,
  type KeepRescanRemovalCommandOutput,
  KeepRescanRemovalCommand,
} from "./commands/KeepRescanRemovalCommand";
import {
  type ListAnswerQualityRunsCommandInput,
  type ListAnswerQualityRunsCommandOutput,
  ListAnswerQualityRunsCommand,
} from "./commands/ListAnswerQualityRunsCommand";
import {
  type ListDictionariesCommandInput,
  type ListDictionariesCommandOutput,
  ListDictionariesCommand,
} from "./commands/ListDictionariesCommand";
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
  type ListFactConflictsCommandInput,
  type ListFactConflictsCommandOutput,
  ListFactConflictsCommand,
} from "./commands/ListFactConflictsCommand";
import {
  type ListFactEventsCommandInput,
  type ListFactEventsCommandOutput,
  ListFactEventsCommand,
} from "./commands/ListFactEventsCommand";
import { type ListFactsCommandInput, type ListFactsCommandOutput, ListFactsCommand } from "./commands/ListFactsCommand";
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
  type ListIngestionRunsCommandInput,
  type ListIngestionRunsCommandOutput,
  ListIngestionRunsCommand,
} from "./commands/ListIngestionRunsCommand";
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
  type ListOntologyEventsCommandInput,
  type ListOntologyEventsCommandOutput,
  ListOntologyEventsCommand,
} from "./commands/ListOntologyEventsCommand";
import {
  type ListOntologyInstancesCommandInput,
  type ListOntologyInstancesCommandOutput,
  ListOntologyInstancesCommand,
} from "./commands/ListOntologyInstancesCommand";
import {
  type ListOntologyProposalsCommandInput,
  type ListOntologyProposalsCommandOutput,
  ListOntologyProposalsCommand,
} from "./commands/ListOntologyProposalsCommand";
import {
  type ListOntologyVersionsCommandInput,
  type ListOntologyVersionsCommandOutput,
  ListOntologyVersionsCommand,
} from "./commands/ListOntologyVersionsCommand";
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
import { type ListTermsCommandInput, type ListTermsCommandOutput, ListTermsCommand } from "./commands/ListTermsCommand";
import {
  type LoadFoundationalOntologyCommandInput,
  type LoadFoundationalOntologyCommandOutput,
  LoadFoundationalOntologyCommand,
} from "./commands/LoadFoundationalOntologyCommand";
import {
  type MaterializeReasoningCommandInput,
  type MaterializeReasoningCommandOutput,
  MaterializeReasoningCommand,
} from "./commands/MaterializeReasoningCommand";
import {
  type ProposeOntologyVersionCommandInput,
  type ProposeOntologyVersionCommandOutput,
  ProposeOntologyVersionCommand,
} from "./commands/ProposeOntologyVersionCommand";
import {
  type PublishOntologyCommandInput,
  type PublishOntologyCommandOutput,
  PublishOntologyCommand,
} from "./commands/PublishOntologyCommand";
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
  type RefreshDictionariesCommandInput,
  type RefreshDictionariesCommandOutput,
  RefreshDictionariesCommand,
} from "./commands/RefreshDictionariesCommand";
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
  type ResolveFactConflictsCommandInput,
  type ResolveFactConflictsCommandOutput,
  ResolveFactConflictsCommand,
} from "./commands/ResolveFactConflictsCommand";
import {
  type RestoreFactCommandInput,
  type RestoreFactCommandOutput,
  RestoreFactCommand,
} from "./commands/RestoreFactCommand";
import {
  type RetractFactCommandInput,
  type RetractFactCommandOutput,
  RetractFactCommand,
} from "./commands/RetractFactCommand";
import {
  type RetractFactsCommandInput,
  type RetractFactsCommandOutput,
  RetractFactsCommand,
} from "./commands/RetractFactsCommand";
import {
  type ReviewOntologyProposalCommandInput,
  type ReviewOntologyProposalCommandOutput,
  ReviewOntologyProposalCommand,
} from "./commands/ReviewOntologyProposalCommand";
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
  type RollbackOntologyCommandInput,
  type RollbackOntologyCommandOutput,
  RollbackOntologyCommand,
} from "./commands/RollbackOntologyCommand";
import {
  type RunValidationCommandInput,
  type RunValidationCommandOutput,
  RunValidationCommand,
} from "./commands/RunValidationCommand";
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
  type StartOntologyValidationCommandInput,
  type StartOntologyValidationCommandOutput,
  StartOntologyValidationCommand,
} from "./commands/StartOntologyValidationCommand";
import {
  type UndoFactConflictResolutionCommandInput,
  type UndoFactConflictResolutionCommandOutput,
  UndoFactConflictResolutionCommand,
} from "./commands/UndoFactConflictResolutionCommand";
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
import {
  type VerifyOntologyCommandInput,
  type VerifyOntologyCommandOutput,
  VerifyOntologyCommand,
} from "./commands/VerifyOntologyCommand";
import { ControlPlaneServiceClient } from "./ControlPlaneServiceClient";
import { paginateListDocumentChunks } from "./pagination/ListDocumentChunksPaginator";
import { paginateListDocuments } from "./pagination/ListDocumentsPaginator";
import { paginateListFactCandidates } from "./pagination/ListFactCandidatesPaginator";
import { paginateListInducedDatasources } from "./pagination/ListInducedDatasourcesPaginator";
import { paginateListInductionJobs } from "./pagination/ListInductionJobsPaginator";
import { paginateListIngestionRuns } from "./pagination/ListIngestionRunsPaginator";
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
  BrowseOntologyTreeCommand,
  ListOntologyInstancesCommand,
  GetDictionaryCommand,
  GetDictionaryCommentCoverageCommand,
  GetDictionaryViewCommand,
  ListDictionariesCommand,
  ListTermsCommand,
  RefreshDictionariesCommand,
  ApproveFactCandidateCommand,
  ListDocumentChunksCommand,
  ListDocumentsCommand,
  ListFactCandidatesCommand,
  RejectFactCandidateCommand,
  UploadDocumentCommand,
  GetEntityEmbeddingsCommand,
  SearchEmbeddingsCommand,
  GetEntityCommand,
  GetEntityProvenanceCommand,
  AssertFactCommand,
  BatchKeepFactConflictsCommand,
  GetFactCommand,
  ListFactConflictsCommand,
  ListFactEventsCommand,
  ListFactsCommand,
  ResolveFactConflictsCommand,
  RestoreFactCommand,
  RetractFactCommand,
  RetractFactsCommand,
  UndoFactConflictResolutionCommand,
  CreateGrantCommand,
  CreatePlatformGrantCommand,
  DeleteGrantCommand,
  DeletePlatformGrantCommand,
  ListNamespaceGrantsCommand,
  ListPlatformGrantsCommand,
  ListPrincipalGrantsCommand,
  ListIngestionRunsCommand,
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
  GetMetricFamilyCommand,
  GetMetricReportManifestCommand,
  CreateNamespaceCommand,
  DeleteNamespaceCommand,
  GetNamespaceCommand,
  ListNamespacesCommand,
  UpdateNamespaceCommand,
  UpdateNamespaceStatusCommand,
  ExportOntologyBundleCommand,
  ImportBundleCommand,
  InspectOntologyBundleCommand,
  DeleteOntologyCommand,
  DownloadOntologyCommand,
  FetchOntologyCommand,
  FindGraphPathCommand,
  FindLinksCommand,
  GetCanvasManifestCommand,
  GetCanvasSubgraphCommand,
  GetGraphClassCommand,
  GetGraphDatatypePropertyCommand,
  GetGraphObjectPropertyCommand,
  GetIngestStatusCommand,
  GetOntologyCommand,
  GetOntologyDiffCommand,
  GetOntologyOverviewCommand,
  GetOntologySnapshotCommand,
  GetOntologyUploadUrlCommand,
  GetReasoningStatusCommand,
  GraphSearchCommand,
  IngestOntologyFromS3Command,
  ListOntologiesCommand,
  ListStatementsCommand,
  MaterializeReasoningCommand,
  RunValidationCommand,
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
  DiffOntologyVersionsCommand,
  ExportOntologyVersionCommand,
  GetOntologyVersionCommand,
  GetOntologyVersionProposalCommand,
  ImportOntologyCommand,
  ListOntologyEventsCommand,
  ListOntologyProposalsCommand,
  ListOntologyVersionsCommand,
  ProposeOntologyVersionCommand,
  PublishOntologyCommand,
  ReviewOntologyProposalCommand,
  RollbackOntologyCommand,
  VerifyOntologyCommand,
  GetOntologyValidationJobCommand,
  StartOntologyValidationCommand,
  GetMetricCardCommand,
  GetAnswerQualityCommand,
  ListAnswerQualityRunsCommand,
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
  paginateListIngestionRuns,
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
   * @see {@link BrowseOntologyTreeCommand}
   */
  browseOntologyTree(): Promise<BrowseOntologyTreeCommandOutput>;
  browseOntologyTree(
    args: BrowseOntologyTreeCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<BrowseOntologyTreeCommandOutput>;
  browseOntologyTree(
    args: BrowseOntologyTreeCommandInput,
    cb: (err: any, data?: BrowseOntologyTreeCommandOutput) => void
  ): void;
  browseOntologyTree(
    args: BrowseOntologyTreeCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: BrowseOntologyTreeCommandOutput) => void
  ): void;

  /**
   * @see {@link ListOntologyInstancesCommand}
   */
  listOntologyInstances(
    args: ListOntologyInstancesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListOntologyInstancesCommandOutput>;
  listOntologyInstances(
    args: ListOntologyInstancesCommandInput,
    cb: (err: any, data?: ListOntologyInstancesCommandOutput) => void
  ): void;
  listOntologyInstances(
    args: ListOntologyInstancesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListOntologyInstancesCommandOutput) => void
  ): void;

  /**
   * @see {@link GetDictionaryCommand}
   */
  getDictionary(
    args: GetDictionaryCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetDictionaryCommandOutput>;
  getDictionary(
    args: GetDictionaryCommandInput,
    cb: (err: any, data?: GetDictionaryCommandOutput) => void
  ): void;
  getDictionary(
    args: GetDictionaryCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetDictionaryCommandOutput) => void
  ): void;

  /**
   * @see {@link GetDictionaryCommentCoverageCommand}
   */
  getDictionaryCommentCoverage(
    args: GetDictionaryCommentCoverageCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetDictionaryCommentCoverageCommandOutput>;
  getDictionaryCommentCoverage(
    args: GetDictionaryCommentCoverageCommandInput,
    cb: (err: any, data?: GetDictionaryCommentCoverageCommandOutput) => void
  ): void;
  getDictionaryCommentCoverage(
    args: GetDictionaryCommentCoverageCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetDictionaryCommentCoverageCommandOutput) => void
  ): void;

  /**
   * @see {@link GetDictionaryViewCommand}
   */
  getDictionaryView(
    args: GetDictionaryViewCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetDictionaryViewCommandOutput>;
  getDictionaryView(
    args: GetDictionaryViewCommandInput,
    cb: (err: any, data?: GetDictionaryViewCommandOutput) => void
  ): void;
  getDictionaryView(
    args: GetDictionaryViewCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetDictionaryViewCommandOutput) => void
  ): void;

  /**
   * @see {@link ListDictionariesCommand}
   */
  listDictionaries(
    args: ListDictionariesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListDictionariesCommandOutput>;
  listDictionaries(
    args: ListDictionariesCommandInput,
    cb: (err: any, data?: ListDictionariesCommandOutput) => void
  ): void;
  listDictionaries(
    args: ListDictionariesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListDictionariesCommandOutput) => void
  ): void;

  /**
   * @see {@link ListTermsCommand}
   */
  listTerms(
    args: ListTermsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListTermsCommandOutput>;
  listTerms(
    args: ListTermsCommandInput,
    cb: (err: any, data?: ListTermsCommandOutput) => void
  ): void;
  listTerms(
    args: ListTermsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListTermsCommandOutput) => void
  ): void;

  /**
   * @see {@link RefreshDictionariesCommand}
   */
  refreshDictionaries(
    args: RefreshDictionariesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RefreshDictionariesCommandOutput>;
  refreshDictionaries(
    args: RefreshDictionariesCommandInput,
    cb: (err: any, data?: RefreshDictionariesCommandOutput) => void
  ): void;
  refreshDictionaries(
    args: RefreshDictionariesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RefreshDictionariesCommandOutput) => void
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
   * @see {@link GetEntityCommand}
   */
  getEntity(
    args: GetEntityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetEntityCommandOutput>;
  getEntity(
    args: GetEntityCommandInput,
    cb: (err: any, data?: GetEntityCommandOutput) => void
  ): void;
  getEntity(
    args: GetEntityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetEntityCommandOutput) => void
  ): void;

  /**
   * @see {@link GetEntityProvenanceCommand}
   */
  getEntityProvenance(
    args: GetEntityProvenanceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetEntityProvenanceCommandOutput>;
  getEntityProvenance(
    args: GetEntityProvenanceCommandInput,
    cb: (err: any, data?: GetEntityProvenanceCommandOutput) => void
  ): void;
  getEntityProvenance(
    args: GetEntityProvenanceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetEntityProvenanceCommandOutput) => void
  ): void;

  /**
   * @see {@link AssertFactCommand}
   */
  assertFact(
    args: AssertFactCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<AssertFactCommandOutput>;
  assertFact(
    args: AssertFactCommandInput,
    cb: (err: any, data?: AssertFactCommandOutput) => void
  ): void;
  assertFact(
    args: AssertFactCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: AssertFactCommandOutput) => void
  ): void;

  /**
   * @see {@link BatchKeepFactConflictsCommand}
   */
  batchKeepFactConflicts(
    args: BatchKeepFactConflictsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<BatchKeepFactConflictsCommandOutput>;
  batchKeepFactConflicts(
    args: BatchKeepFactConflictsCommandInput,
    cb: (err: any, data?: BatchKeepFactConflictsCommandOutput) => void
  ): void;
  batchKeepFactConflicts(
    args: BatchKeepFactConflictsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: BatchKeepFactConflictsCommandOutput) => void
  ): void;

  /**
   * @see {@link GetFactCommand}
   */
  getFact(
    args: GetFactCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetFactCommandOutput>;
  getFact(
    args: GetFactCommandInput,
    cb: (err: any, data?: GetFactCommandOutput) => void
  ): void;
  getFact(
    args: GetFactCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetFactCommandOutput) => void
  ): void;

  /**
   * @see {@link ListFactConflictsCommand}
   */
  listFactConflicts(
    args: ListFactConflictsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListFactConflictsCommandOutput>;
  listFactConflicts(
    args: ListFactConflictsCommandInput,
    cb: (err: any, data?: ListFactConflictsCommandOutput) => void
  ): void;
  listFactConflicts(
    args: ListFactConflictsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListFactConflictsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListFactEventsCommand}
   */
  listFactEvents(
    args: ListFactEventsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListFactEventsCommandOutput>;
  listFactEvents(
    args: ListFactEventsCommandInput,
    cb: (err: any, data?: ListFactEventsCommandOutput) => void
  ): void;
  listFactEvents(
    args: ListFactEventsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListFactEventsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListFactsCommand}
   */
  listFacts(
    args: ListFactsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListFactsCommandOutput>;
  listFacts(
    args: ListFactsCommandInput,
    cb: (err: any, data?: ListFactsCommandOutput) => void
  ): void;
  listFacts(
    args: ListFactsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListFactsCommandOutput) => void
  ): void;

  /**
   * @see {@link ResolveFactConflictsCommand}
   */
  resolveFactConflicts(
    args: ResolveFactConflictsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ResolveFactConflictsCommandOutput>;
  resolveFactConflicts(
    args: ResolveFactConflictsCommandInput,
    cb: (err: any, data?: ResolveFactConflictsCommandOutput) => void
  ): void;
  resolveFactConflicts(
    args: ResolveFactConflictsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ResolveFactConflictsCommandOutput) => void
  ): void;

  /**
   * @see {@link RestoreFactCommand}
   */
  restoreFact(
    args: RestoreFactCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RestoreFactCommandOutput>;
  restoreFact(
    args: RestoreFactCommandInput,
    cb: (err: any, data?: RestoreFactCommandOutput) => void
  ): void;
  restoreFact(
    args: RestoreFactCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RestoreFactCommandOutput) => void
  ): void;

  /**
   * @see {@link RetractFactCommand}
   */
  retractFact(
    args: RetractFactCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RetractFactCommandOutput>;
  retractFact(
    args: RetractFactCommandInput,
    cb: (err: any, data?: RetractFactCommandOutput) => void
  ): void;
  retractFact(
    args: RetractFactCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RetractFactCommandOutput) => void
  ): void;

  /**
   * @see {@link RetractFactsCommand}
   */
  retractFacts(
    args: RetractFactsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RetractFactsCommandOutput>;
  retractFacts(
    args: RetractFactsCommandInput,
    cb: (err: any, data?: RetractFactsCommandOutput) => void
  ): void;
  retractFacts(
    args: RetractFactsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RetractFactsCommandOutput) => void
  ): void;

  /**
   * @see {@link UndoFactConflictResolutionCommand}
   */
  undoFactConflictResolution(
    args: UndoFactConflictResolutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UndoFactConflictResolutionCommandOutput>;
  undoFactConflictResolution(
    args: UndoFactConflictResolutionCommandInput,
    cb: (err: any, data?: UndoFactConflictResolutionCommandOutput) => void
  ): void;
  undoFactConflictResolution(
    args: UndoFactConflictResolutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UndoFactConflictResolutionCommandOutput) => void
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
   * @see {@link ListIngestionRunsCommand}
   */
  listIngestionRuns(
    args: ListIngestionRunsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListIngestionRunsCommandOutput>;
  listIngestionRuns(
    args: ListIngestionRunsCommandInput,
    cb: (err: any, data?: ListIngestionRunsCommandOutput) => void
  ): void;
  listIngestionRuns(
    args: ListIngestionRunsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListIngestionRunsCommandOutput) => void
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
   * @see {@link GetMetricFamilyCommand}
   */
  getMetricFamily(
    args: GetMetricFamilyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetMetricFamilyCommandOutput>;
  getMetricFamily(
    args: GetMetricFamilyCommandInput,
    cb: (err: any, data?: GetMetricFamilyCommandOutput) => void
  ): void;
  getMetricFamily(
    args: GetMetricFamilyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetMetricFamilyCommandOutput) => void
  ): void;

  /**
   * @see {@link GetMetricReportManifestCommand}
   */
  getMetricReportManifest(
    args: GetMetricReportManifestCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetMetricReportManifestCommandOutput>;
  getMetricReportManifest(
    args: GetMetricReportManifestCommandInput,
    cb: (err: any, data?: GetMetricReportManifestCommandOutput) => void
  ): void;
  getMetricReportManifest(
    args: GetMetricReportManifestCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetMetricReportManifestCommandOutput) => void
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
   * @see {@link ExportOntologyBundleCommand}
   */
  exportOntologyBundle(
    args: ExportOntologyBundleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ExportOntologyBundleCommandOutput>;
  exportOntologyBundle(
    args: ExportOntologyBundleCommandInput,
    cb: (err: any, data?: ExportOntologyBundleCommandOutput) => void
  ): void;
  exportOntologyBundle(
    args: ExportOntologyBundleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ExportOntologyBundleCommandOutput) => void
  ): void;

  /**
   * @see {@link ImportBundleCommand}
   */
  importBundle(
    args: ImportBundleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ImportBundleCommandOutput>;
  importBundle(
    args: ImportBundleCommandInput,
    cb: (err: any, data?: ImportBundleCommandOutput) => void
  ): void;
  importBundle(
    args: ImportBundleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ImportBundleCommandOutput) => void
  ): void;

  /**
   * @see {@link InspectOntologyBundleCommand}
   */
  inspectOntologyBundle(
    args: InspectOntologyBundleCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<InspectOntologyBundleCommandOutput>;
  inspectOntologyBundle(
    args: InspectOntologyBundleCommandInput,
    cb: (err: any, data?: InspectOntologyBundleCommandOutput) => void
  ): void;
  inspectOntologyBundle(
    args: InspectOntologyBundleCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: InspectOntologyBundleCommandOutput) => void
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
   * @see {@link FindGraphPathCommand}
   */
  findGraphPath(
    args: FindGraphPathCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<FindGraphPathCommandOutput>;
  findGraphPath(
    args: FindGraphPathCommandInput,
    cb: (err: any, data?: FindGraphPathCommandOutput) => void
  ): void;
  findGraphPath(
    args: FindGraphPathCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: FindGraphPathCommandOutput) => void
  ): void;

  /**
   * @see {@link FindLinksCommand}
   */
  findLinks(
    args: FindLinksCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<FindLinksCommandOutput>;
  findLinks(
    args: FindLinksCommandInput,
    cb: (err: any, data?: FindLinksCommandOutput) => void
  ): void;
  findLinks(
    args: FindLinksCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: FindLinksCommandOutput) => void
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
   * @see {@link GetCanvasSubgraphCommand}
   */
  getCanvasSubgraph(
    args: GetCanvasSubgraphCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetCanvasSubgraphCommandOutput>;
  getCanvasSubgraph(
    args: GetCanvasSubgraphCommandInput,
    cb: (err: any, data?: GetCanvasSubgraphCommandOutput) => void
  ): void;
  getCanvasSubgraph(
    args: GetCanvasSubgraphCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetCanvasSubgraphCommandOutput) => void
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
   * @see {@link GetOntologyDiffCommand}
   */
  getOntologyDiff(
    args: GetOntologyDiffCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyDiffCommandOutput>;
  getOntologyDiff(
    args: GetOntologyDiffCommandInput,
    cb: (err: any, data?: GetOntologyDiffCommandOutput) => void
  ): void;
  getOntologyDiff(
    args: GetOntologyDiffCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyDiffCommandOutput) => void
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
   * @see {@link GetOntologySnapshotCommand}
   */
  getOntologySnapshot(
    args: GetOntologySnapshotCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologySnapshotCommandOutput>;
  getOntologySnapshot(
    args: GetOntologySnapshotCommandInput,
    cb: (err: any, data?: GetOntologySnapshotCommandOutput) => void
  ): void;
  getOntologySnapshot(
    args: GetOntologySnapshotCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologySnapshotCommandOutput) => void
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
   * @see {@link GetReasoningStatusCommand}
   */
  getReasoningStatus(
    args: GetReasoningStatusCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetReasoningStatusCommandOutput>;
  getReasoningStatus(
    args: GetReasoningStatusCommandInput,
    cb: (err: any, data?: GetReasoningStatusCommandOutput) => void
  ): void;
  getReasoningStatus(
    args: GetReasoningStatusCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetReasoningStatusCommandOutput) => void
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
   * @see {@link MaterializeReasoningCommand}
   */
  materializeReasoning(
    args: MaterializeReasoningCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<MaterializeReasoningCommandOutput>;
  materializeReasoning(
    args: MaterializeReasoningCommandInput,
    cb: (err: any, data?: MaterializeReasoningCommandOutput) => void
  ): void;
  materializeReasoning(
    args: MaterializeReasoningCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: MaterializeReasoningCommandOutput) => void
  ): void;

  /**
   * @see {@link RunValidationCommand}
   */
  runValidation(
    args: RunValidationCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RunValidationCommandOutput>;
  runValidation(
    args: RunValidationCommandInput,
    cb: (err: any, data?: RunValidationCommandOutput) => void
  ): void;
  runValidation(
    args: RunValidationCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RunValidationCommandOutput) => void
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
   * @see {@link DiffOntologyVersionsCommand}
   */
  diffOntologyVersions(
    args: DiffOntologyVersionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DiffOntologyVersionsCommandOutput>;
  diffOntologyVersions(
    args: DiffOntologyVersionsCommandInput,
    cb: (err: any, data?: DiffOntologyVersionsCommandOutput) => void
  ): void;
  diffOntologyVersions(
    args: DiffOntologyVersionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DiffOntologyVersionsCommandOutput) => void
  ): void;

  /**
   * @see {@link ExportOntologyVersionCommand}
   */
  exportOntologyVersion(
    args: ExportOntologyVersionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ExportOntologyVersionCommandOutput>;
  exportOntologyVersion(
    args: ExportOntologyVersionCommandInput,
    cb: (err: any, data?: ExportOntologyVersionCommandOutput) => void
  ): void;
  exportOntologyVersion(
    args: ExportOntologyVersionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ExportOntologyVersionCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOntologyVersionCommand}
   */
  getOntologyVersion(
    args: GetOntologyVersionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyVersionCommandOutput>;
  getOntologyVersion(
    args: GetOntologyVersionCommandInput,
    cb: (err: any, data?: GetOntologyVersionCommandOutput) => void
  ): void;
  getOntologyVersion(
    args: GetOntologyVersionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyVersionCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOntologyVersionProposalCommand}
   */
  getOntologyVersionProposal(
    args: GetOntologyVersionProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyVersionProposalCommandOutput>;
  getOntologyVersionProposal(
    args: GetOntologyVersionProposalCommandInput,
    cb: (err: any, data?: GetOntologyVersionProposalCommandOutput) => void
  ): void;
  getOntologyVersionProposal(
    args: GetOntologyVersionProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyVersionProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link ImportOntologyCommand}
   */
  importOntology(
    args: ImportOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ImportOntologyCommandOutput>;
  importOntology(
    args: ImportOntologyCommandInput,
    cb: (err: any, data?: ImportOntologyCommandOutput) => void
  ): void;
  importOntology(
    args: ImportOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ImportOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link ListOntologyEventsCommand}
   */
  listOntologyEvents(
    args: ListOntologyEventsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListOntologyEventsCommandOutput>;
  listOntologyEvents(
    args: ListOntologyEventsCommandInput,
    cb: (err: any, data?: ListOntologyEventsCommandOutput) => void
  ): void;
  listOntologyEvents(
    args: ListOntologyEventsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListOntologyEventsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListOntologyProposalsCommand}
   */
  listOntologyProposals(
    args: ListOntologyProposalsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListOntologyProposalsCommandOutput>;
  listOntologyProposals(
    args: ListOntologyProposalsCommandInput,
    cb: (err: any, data?: ListOntologyProposalsCommandOutput) => void
  ): void;
  listOntologyProposals(
    args: ListOntologyProposalsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListOntologyProposalsCommandOutput) => void
  ): void;

  /**
   * @see {@link ListOntologyVersionsCommand}
   */
  listOntologyVersions(
    args: ListOntologyVersionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListOntologyVersionsCommandOutput>;
  listOntologyVersions(
    args: ListOntologyVersionsCommandInput,
    cb: (err: any, data?: ListOntologyVersionsCommandOutput) => void
  ): void;
  listOntologyVersions(
    args: ListOntologyVersionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListOntologyVersionsCommandOutput) => void
  ): void;

  /**
   * @see {@link ProposeOntologyVersionCommand}
   */
  proposeOntologyVersion(
    args: ProposeOntologyVersionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ProposeOntologyVersionCommandOutput>;
  proposeOntologyVersion(
    args: ProposeOntologyVersionCommandInput,
    cb: (err: any, data?: ProposeOntologyVersionCommandOutput) => void
  ): void;
  proposeOntologyVersion(
    args: ProposeOntologyVersionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ProposeOntologyVersionCommandOutput) => void
  ): void;

  /**
   * @see {@link PublishOntologyCommand}
   */
  publishOntology(
    args: PublishOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<PublishOntologyCommandOutput>;
  publishOntology(
    args: PublishOntologyCommandInput,
    cb: (err: any, data?: PublishOntologyCommandOutput) => void
  ): void;
  publishOntology(
    args: PublishOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: PublishOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link ReviewOntologyProposalCommand}
   */
  reviewOntologyProposal(
    args: ReviewOntologyProposalCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ReviewOntologyProposalCommandOutput>;
  reviewOntologyProposal(
    args: ReviewOntologyProposalCommandInput,
    cb: (err: any, data?: ReviewOntologyProposalCommandOutput) => void
  ): void;
  reviewOntologyProposal(
    args: ReviewOntologyProposalCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ReviewOntologyProposalCommandOutput) => void
  ): void;

  /**
   * @see {@link RollbackOntologyCommand}
   */
  rollbackOntology(
    args: RollbackOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RollbackOntologyCommandOutput>;
  rollbackOntology(
    args: RollbackOntologyCommandInput,
    cb: (err: any, data?: RollbackOntologyCommandOutput) => void
  ): void;
  rollbackOntology(
    args: RollbackOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RollbackOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link VerifyOntologyCommand}
   */
  verifyOntology(
    args: VerifyOntologyCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<VerifyOntologyCommandOutput>;
  verifyOntology(
    args: VerifyOntologyCommandInput,
    cb: (err: any, data?: VerifyOntologyCommandOutput) => void
  ): void;
  verifyOntology(
    args: VerifyOntologyCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: VerifyOntologyCommandOutput) => void
  ): void;

  /**
   * @see {@link GetOntologyValidationJobCommand}
   */
  getOntologyValidationJob(
    args: GetOntologyValidationJobCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetOntologyValidationJobCommandOutput>;
  getOntologyValidationJob(
    args: GetOntologyValidationJobCommandInput,
    cb: (err: any, data?: GetOntologyValidationJobCommandOutput) => void
  ): void;
  getOntologyValidationJob(
    args: GetOntologyValidationJobCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetOntologyValidationJobCommandOutput) => void
  ): void;

  /**
   * @see {@link StartOntologyValidationCommand}
   */
  startOntologyValidation(
    args: StartOntologyValidationCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<StartOntologyValidationCommandOutput>;
  startOntologyValidation(
    args: StartOntologyValidationCommandInput,
    cb: (err: any, data?: StartOntologyValidationCommandOutput) => void
  ): void;
  startOntologyValidation(
    args: StartOntologyValidationCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: StartOntologyValidationCommandOutput) => void
  ): void;

  /**
   * @see {@link GetMetricCardCommand}
   */
  getMetricCard(
    args: GetMetricCardCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetMetricCardCommandOutput>;
  getMetricCard(
    args: GetMetricCardCommandInput,
    cb: (err: any, data?: GetMetricCardCommandOutput) => void
  ): void;
  getMetricCard(
    args: GetMetricCardCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetMetricCardCommandOutput) => void
  ): void;

  /**
   * @see {@link GetAnswerQualityCommand}
   */
  getAnswerQuality(
    args: GetAnswerQualityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetAnswerQualityCommandOutput>;
  getAnswerQuality(
    args: GetAnswerQualityCommandInput,
    cb: (err: any, data?: GetAnswerQualityCommandOutput) => void
  ): void;
  getAnswerQuality(
    args: GetAnswerQualityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetAnswerQualityCommandOutput) => void
  ): void;

  /**
   * @see {@link ListAnswerQualityRunsCommand}
   */
  listAnswerQualityRuns(): Promise<ListAnswerQualityRunsCommandOutput>;
  listAnswerQualityRuns(
    args: ListAnswerQualityRunsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListAnswerQualityRunsCommandOutput>;
  listAnswerQualityRuns(
    args: ListAnswerQualityRunsCommandInput,
    cb: (err: any, data?: ListAnswerQualityRunsCommandOutput) => void
  ): void;
  listAnswerQualityRuns(
    args: ListAnswerQualityRunsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListAnswerQualityRunsCommandOutput) => void
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
   * @see {@link ListIngestionRunsCommand}
   * @param args - command input.
   * @param paginationConfig - optional pagination config.
   * @returns AsyncIterable of {@link ListIngestionRunsCommandOutput}.
   */
  paginateListIngestionRuns(
    args: ListIngestionRunsCommandInput,
    paginationConfig?: Omit<PaginationConfiguration, "client">
  ): Paginator<ListIngestionRunsCommandOutput>;

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
