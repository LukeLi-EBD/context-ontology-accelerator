// smithy-typescript generated code
import {
  type HostHeaderInputConfig,
  type HostHeaderResolvedConfig,
  getHostHeaderPlugin,
  resolveHostHeaderConfig,
} from "@aws-sdk/middleware-host-header";
import { getLoggerPlugin } from "@aws-sdk/middleware-logger";
import { getRecursionDetectionPlugin } from "@aws-sdk/middleware-recursion-detection";
import {
  type UserAgentInputConfig,
  type UserAgentResolvedConfig,
  getUserAgentPlugin,
  resolveUserAgentConfig,
} from "@aws-sdk/middleware-user-agent";
import {
  DefaultIdentityProviderConfig,
  getHttpAuthSchemeEndpointRuleSetPlugin,
  getHttpSigningPlugin,
} from "@smithy/core";
import { getSchemaSerdePlugin } from "@smithy/core/schema";
import { getContentLengthPlugin } from "@smithy/middleware-content-length";
import {
  type EndpointInputConfig,
  type EndpointRequiredInputConfig,
  type EndpointRequiredResolvedConfig,
  type EndpointResolvedConfig,
  resolveEndpointConfig,
  resolveEndpointRequiredConfig,
} from "@smithy/middleware-endpoint";
import {
  type RetryInputConfig,
  type RetryResolvedConfig,
  getRetryPlugin,
  resolveRetryConfig,
} from "@smithy/middleware-retry";
import type { HttpHandlerUserInput as __HttpHandlerUserInput } from "@smithy/protocol-http";
import {
  type DefaultsMode as __DefaultsMode,
  type SmithyConfiguration as __SmithyConfiguration,
  type SmithyResolvedConfiguration as __SmithyResolvedConfiguration,
  Client as __Client,
} from "@smithy/smithy-client";
import type {
  BodyLengthCalculator as __BodyLengthCalculator,
  CheckOptionalClientConfig as __CheckOptionalClientConfig,
  ChecksumConstructor as __ChecksumConstructor,
  Decoder as __Decoder,
  Encoder as __Encoder,
  HashConstructor as __HashConstructor,
  HttpHandlerOptions as __HttpHandlerOptions,
  Logger as __Logger,
  Provider as __Provider,
  StreamCollector as __StreamCollector,
  UrlParser as __UrlParser,
  UserAgent as __UserAgent,
} from "@smithy/types";

import {
  type HttpAuthSchemeInputConfig,
  type HttpAuthSchemeResolvedConfig,
  defaultControlPlaneServiceHttpAuthSchemeParametersProvider,
  resolveHttpAuthSchemeConfig,
} from "./auth/httpAuthSchemeProvider";
import type { AcceptProposalCommandInput, AcceptProposalCommandOutput } from "./commands/AcceptProposalCommand";
import type {
  ApproveFactCandidateCommandInput,
  ApproveFactCandidateCommandOutput,
} from "./commands/ApproveFactCandidateCommand";
import type { ApproveSourceCommandInput, ApproveSourceCommandOutput } from "./commands/ApproveSourceCommand";
import type { AssertFactCommandInput, AssertFactCommandOutput } from "./commands/AssertFactCommand";
import type {
  BatchKeepFactConflictsCommandInput,
  BatchKeepFactConflictsCommandOutput,
} from "./commands/BatchKeepFactConflictsCommand";
import type {
  BrowseOntologyTreeCommandInput,
  BrowseOntologyTreeCommandOutput,
} from "./commands/BrowseOntologyTreeCommand";
import type {
  BulkDeleteMetricsCommandInput,
  BulkDeleteMetricsCommandOutput,
} from "./commands/BulkDeleteMetricsCommand";
import type { CancelProposalCommandInput, CancelProposalCommandOutput } from "./commands/CancelProposalCommand";
import type {
  CompileConstraintsCommandInput,
  CompileConstraintsCommandOutput,
} from "./commands/CompileConstraintsCommand";
import type { CreateGrantCommandInput, CreateGrantCommandOutput } from "./commands/CreateGrantCommand";
import type { CreateMetricCommandInput, CreateMetricCommandOutput } from "./commands/CreateMetricCommand";
import type { CreateNamespaceCommandInput, CreateNamespaceCommandOutput } from "./commands/CreateNamespaceCommand";
import type {
  CreatePlatformGrantCommandInput,
  CreatePlatformGrantCommandOutput,
} from "./commands/CreatePlatformGrantCommand";
import type { CreateSourceCommandInput, CreateSourceCommandOutput } from "./commands/CreateSourceCommand";
import type { DeleteGrantCommandInput, DeleteGrantCommandOutput } from "./commands/DeleteGrantCommand";
import type { DeleteMetricCommandInput, DeleteMetricCommandOutput } from "./commands/DeleteMetricCommand";
import type { DeleteNamespaceCommandInput, DeleteNamespaceCommandOutput } from "./commands/DeleteNamespaceCommand";
import type { DeleteOntologyCommandInput, DeleteOntologyCommandOutput } from "./commands/DeleteOntologyCommand";
import type {
  DeletePlatformGrantCommandInput,
  DeletePlatformGrantCommandOutput,
} from "./commands/DeletePlatformGrantCommand";
import type { DeleteSourceCommandInput, DeleteSourceCommandOutput } from "./commands/DeleteSourceCommand";
import type {
  DiffOntologyVersionsCommandInput,
  DiffOntologyVersionsCommandOutput,
} from "./commands/DiffOntologyVersionsCommand";
import type { DownloadOntologyCommandInput, DownloadOntologyCommandOutput } from "./commands/DownloadOntologyCommand";
import type {
  ExportOntologyBundleCommandInput,
  ExportOntologyBundleCommandOutput,
} from "./commands/ExportOntologyBundleCommand";
import type {
  ExportOntologyVersionCommandInput,
  ExportOntologyVersionCommandOutput,
} from "./commands/ExportOntologyVersionCommand";
import type { ExportOsiCommandInput, ExportOsiCommandOutput } from "./commands/ExportOsiCommand";
import type { FetchOntologyCommandInput, FetchOntologyCommandOutput } from "./commands/FetchOntologyCommand";
import type { FindGraphPathCommandInput, FindGraphPathCommandOutput } from "./commands/FindGraphPathCommand";
import type { FindLinksCommandInput, FindLinksCommandOutput } from "./commands/FindLinksCommand";
import type { GetAnswerQualityCommandInput, GetAnswerQualityCommandOutput } from "./commands/GetAnswerQualityCommand";
import type {
  GetCanvasManifestCommandInput,
  GetCanvasManifestCommandOutput,
} from "./commands/GetCanvasManifestCommand";
import type {
  GetCanvasSubgraphCommandInput,
  GetCanvasSubgraphCommandOutput,
} from "./commands/GetCanvasSubgraphCommand";
import type { GetDictionaryCommandInput, GetDictionaryCommandOutput } from "./commands/GetDictionaryCommand";
import type {
  GetDictionaryCommentCoverageCommandInput,
  GetDictionaryCommentCoverageCommandOutput,
} from "./commands/GetDictionaryCommentCoverageCommand";
import type {
  GetDictionaryViewCommandInput,
  GetDictionaryViewCommandOutput,
} from "./commands/GetDictionaryViewCommand";
import type { GetEntityCommandInput, GetEntityCommandOutput } from "./commands/GetEntityCommand";
import type {
  GetEntityEmbeddingsCommandInput,
  GetEntityEmbeddingsCommandOutput,
} from "./commands/GetEntityEmbeddingsCommand";
import type {
  GetEntityProvenanceCommandInput,
  GetEntityProvenanceCommandOutput,
} from "./commands/GetEntityProvenanceCommand";
import type { GetFactCommandInput, GetFactCommandOutput } from "./commands/GetFactCommand";
import type { GetGraphClassCommandInput, GetGraphClassCommandOutput } from "./commands/GetGraphClassCommand";
import type {
  GetGraphDatatypePropertyCommandInput,
  GetGraphDatatypePropertyCommandOutput,
} from "./commands/GetGraphDatatypePropertyCommand";
import type {
  GetGraphObjectPropertyCommandInput,
  GetGraphObjectPropertyCommandOutput,
} from "./commands/GetGraphObjectPropertyCommand";
import type { GetImportJobCommandInput, GetImportJobCommandOutput } from "./commands/GetImportJobCommand";
import type { GetInductionJobCommandInput, GetInductionJobCommandOutput } from "./commands/GetInductionJobCommand";
import type {
  GetInferConstraintsJobCommandInput,
  GetInferConstraintsJobCommandOutput,
} from "./commands/GetInferConstraintsJobCommand";
import type { GetIngestionRunCommandInput, GetIngestionRunCommandOutput } from "./commands/GetIngestionRunCommand";
import type { GetIngestStatusCommandInput, GetIngestStatusCommandOutput } from "./commands/GetIngestStatusCommand";
import type { GetMetricCardCommandInput, GetMetricCardCommandOutput } from "./commands/GetMetricCardCommand";
import type { GetMetricCommandInput, GetMetricCommandOutput } from "./commands/GetMetricCommand";
import type { GetMetricFamilyCommandInput, GetMetricFamilyCommandOutput } from "./commands/GetMetricFamilyCommand";
import type {
  GetMetricReportManifestCommandInput,
  GetMetricReportManifestCommandOutput,
} from "./commands/GetMetricReportManifestCommand";
import type { GetNamespaceCommandInput, GetNamespaceCommandOutput } from "./commands/GetNamespaceCommand";
import type { GetNamespaceRoleCommandInput, GetNamespaceRoleCommandOutput } from "./commands/GetNamespaceRoleCommand";
import type { GetOntologyCommandInput, GetOntologyCommandOutput } from "./commands/GetOntologyCommand";
import type { GetOntologyDiffCommandInput, GetOntologyDiffCommandOutput } from "./commands/GetOntologyDiffCommand";
import type {
  GetOntologyOverviewCommandInput,
  GetOntologyOverviewCommandOutput,
} from "./commands/GetOntologyOverviewCommand";
import type {
  GetOntologySnapshotCommandInput,
  GetOntologySnapshotCommandOutput,
} from "./commands/GetOntologySnapshotCommand";
import type {
  GetOntologyUploadUrlCommandInput,
  GetOntologyUploadUrlCommandOutput,
} from "./commands/GetOntologyUploadUrlCommand";
import type {
  GetOntologyValidationJobCommandInput,
  GetOntologyValidationJobCommandOutput,
} from "./commands/GetOntologyValidationJobCommand";
import type {
  GetOntologyVersionCommandInput,
  GetOntologyVersionCommandOutput,
} from "./commands/GetOntologyVersionCommand";
import type {
  GetOntologyVersionProposalCommandInput,
  GetOntologyVersionProposalCommandOutput,
} from "./commands/GetOntologyVersionProposalCommand";
import type { GetOsiUploadUrlCommandInput, GetOsiUploadUrlCommandOutput } from "./commands/GetOsiUploadUrlCommand";
import type { GetProposalCommandInput, GetProposalCommandOutput } from "./commands/GetProposalCommand";
import type {
  GetProposalUploadUrlsCommandInput,
  GetProposalUploadUrlsCommandOutput,
} from "./commands/GetProposalUploadUrlsCommand";
import type {
  GetProposalValidationJobCommandInput,
  GetProposalValidationJobCommandOutput,
} from "./commands/GetProposalValidationJobCommand";
import type {
  GetReasoningStatusCommandInput,
  GetReasoningStatusCommandOutput,
} from "./commands/GetReasoningStatusCommand";
import type { GetSourceCommandInput, GetSourceCommandOutput } from "./commands/GetSourceCommand";
import type { GetSourceScanJobCommandInput, GetSourceScanJobCommandOutput } from "./commands/GetSourceScanJobCommand";
import type { GetSourceTableCommandInput, GetSourceTableCommandOutput } from "./commands/GetSourceTableCommand";
import type {
  GetSourceUploadUrlsCommandInput,
  GetSourceUploadUrlsCommandOutput,
} from "./commands/GetSourceUploadUrlsCommand";
import type { GetSystemHealthCommandInput, GetSystemHealthCommandOutput } from "./commands/GetSystemHealthCommand";
import type { GraphSearchCommandInput, GraphSearchCommandOutput } from "./commands/GraphSearchCommand";
import type { HealthCheckCommandInput, HealthCheckCommandOutput } from "./commands/HealthCheckCommand";
import type { ImportBundleCommandInput, ImportBundleCommandOutput } from "./commands/ImportBundleCommand";
import type { ImportOntologyCommandInput, ImportOntologyCommandOutput } from "./commands/ImportOntologyCommand";
import type { ImportOsiCommandInput, ImportOsiCommandOutput } from "./commands/ImportOsiCommand";
import type { InferConstraintsCommandInput, InferConstraintsCommandOutput } from "./commands/InferConstraintsCommand";
import type {
  IngestOntologyFromS3CommandInput,
  IngestOntologyFromS3CommandOutput,
} from "./commands/IngestOntologyFromS3Command";
import type {
  InspectOntologyBundleCommandInput,
  InspectOntologyBundleCommandOutput,
} from "./commands/InspectOntologyBundleCommand";
import type {
  KeepRescanRemovalCommandInput,
  KeepRescanRemovalCommandOutput,
} from "./commands/KeepRescanRemovalCommand";
import type {
  ListAnswerQualityRunsCommandInput,
  ListAnswerQualityRunsCommandOutput,
} from "./commands/ListAnswerQualityRunsCommand";
import type { ListDictionariesCommandInput, ListDictionariesCommandOutput } from "./commands/ListDictionariesCommand";
import type {
  ListDocumentChunksCommandInput,
  ListDocumentChunksCommandOutput,
} from "./commands/ListDocumentChunksCommand";
import type { ListDocumentsCommandInput, ListDocumentsCommandOutput } from "./commands/ListDocumentsCommand";
import type {
  ListFactCandidatesCommandInput,
  ListFactCandidatesCommandOutput,
} from "./commands/ListFactCandidatesCommand";
import type {
  ListFactConflictsCommandInput,
  ListFactConflictsCommandOutput,
} from "./commands/ListFactConflictsCommand";
import type { ListFactEventsCommandInput, ListFactEventsCommandOutput } from "./commands/ListFactEventsCommand";
import type { ListFactsCommandInput, ListFactsCommandOutput } from "./commands/ListFactsCommand";
import type {
  ListFoundationalOntologiesCommandInput,
  ListFoundationalOntologiesCommandOutput,
} from "./commands/ListFoundationalOntologiesCommand";
import type {
  ListInducedDatasourcesCommandInput,
  ListInducedDatasourcesCommandOutput,
} from "./commands/ListInducedDatasourcesCommand";
import type {
  ListInductionJobsCommandInput,
  ListInductionJobsCommandOutput,
} from "./commands/ListInductionJobsCommand";
import type {
  ListIngestionRunsCommandInput,
  ListIngestionRunsCommandOutput,
} from "./commands/ListIngestionRunsCommand";
import type { ListMetricsCommandInput, ListMetricsCommandOutput } from "./commands/ListMetricsCommand";
import type {
  ListNamespaceGrantsCommandInput,
  ListNamespaceGrantsCommandOutput,
} from "./commands/ListNamespaceGrantsCommand";
import type {
  ListNamespaceRolesCommandInput,
  ListNamespaceRolesCommandOutput,
} from "./commands/ListNamespaceRolesCommand";
import type { ListNamespacesCommandInput, ListNamespacesCommandOutput } from "./commands/ListNamespacesCommand";
import type { ListOntologiesCommandInput, ListOntologiesCommandOutput } from "./commands/ListOntologiesCommand";
import type {
  ListOntologyEventsCommandInput,
  ListOntologyEventsCommandOutput,
} from "./commands/ListOntologyEventsCommand";
import type {
  ListOntologyInstancesCommandInput,
  ListOntologyInstancesCommandOutput,
} from "./commands/ListOntologyInstancesCommand";
import type {
  ListOntologyProposalsCommandInput,
  ListOntologyProposalsCommandOutput,
} from "./commands/ListOntologyProposalsCommand";
import type {
  ListOntologyVersionsCommandInput,
  ListOntologyVersionsCommandOutput,
} from "./commands/ListOntologyVersionsCommand";
import type {
  ListPlatformGrantsCommandInput,
  ListPlatformGrantsCommandOutput,
} from "./commands/ListPlatformGrantsCommand";
import type {
  ListPlatformRolesCommandInput,
  ListPlatformRolesCommandOutput,
} from "./commands/ListPlatformRolesCommand";
import type {
  ListPrincipalGrantsCommandInput,
  ListPrincipalGrantsCommandOutput,
} from "./commands/ListPrincipalGrantsCommand";
import type { ListProposalsCommandInput, ListProposalsCommandOutput } from "./commands/ListProposalsCommand";
import type {
  ListSourceScanJobsCommandInput,
  ListSourceScanJobsCommandOutput,
} from "./commands/ListSourceScanJobsCommand";
import type { ListSourcesCommandInput, ListSourcesCommandOutput } from "./commands/ListSourcesCommand";
import type { ListSourceTablesCommandInput, ListSourceTablesCommandOutput } from "./commands/ListSourceTablesCommand";
import type { ListStatementsCommandInput, ListStatementsCommandOutput } from "./commands/ListStatementsCommand";
import type { ListTermsCommandInput, ListTermsCommandOutput } from "./commands/ListTermsCommand";
import type {
  LoadFoundationalOntologyCommandInput,
  LoadFoundationalOntologyCommandOutput,
} from "./commands/LoadFoundationalOntologyCommand";
import type {
  MaterializeReasoningCommandInput,
  MaterializeReasoningCommandOutput,
} from "./commands/MaterializeReasoningCommand";
import type {
  ProposeOntologyVersionCommandInput,
  ProposeOntologyVersionCommandOutput,
} from "./commands/ProposeOntologyVersionCommand";
import type { PublishOntologyCommandInput, PublishOntologyCommandOutput } from "./commands/PublishOntologyCommand";
import type {
  PutSourceEventRescanCommandInput,
  PutSourceEventRescanCommandOutput,
} from "./commands/PutSourceEventRescanCommand";
import type {
  PutSourceRescanScheduleCommandInput,
  PutSourceRescanScheduleCommandOutput,
} from "./commands/PutSourceRescanScheduleCommand";
import type {
  RefreshDictionariesCommandInput,
  RefreshDictionariesCommandOutput,
} from "./commands/RefreshDictionariesCommand";
import type {
  RejectFactCandidateCommandInput,
  RejectFactCandidateCommandOutput,
} from "./commands/RejectFactCandidateCommand";
import type { RejectProposalsCommandInput, RejectProposalsCommandOutput } from "./commands/RejectProposalsCommand";
import type { RejectSourceCommandInput, RejectSourceCommandOutput } from "./commands/RejectSourceCommand";
import type {
  RepairProposalDatatypesCommandInput,
  RepairProposalDatatypesCommandOutput,
} from "./commands/RepairProposalDatatypesCommand";
import type { RescanSourceCommandInput, RescanSourceCommandOutput } from "./commands/RescanSourceCommand";
import type {
  ResolveFactConflictsCommandInput,
  ResolveFactConflictsCommandOutput,
} from "./commands/ResolveFactConflictsCommand";
import type { RestoreFactCommandInput, RestoreFactCommandOutput } from "./commands/RestoreFactCommand";
import type { RetractFactCommandInput, RetractFactCommandOutput } from "./commands/RetractFactCommand";
import type { RetractFactsCommandInput, RetractFactsCommandOutput } from "./commands/RetractFactsCommand";
import type {
  ReviewOntologyProposalCommandInput,
  ReviewOntologyProposalCommandOutput,
} from "./commands/ReviewOntologyProposalCommand";
import type {
  ReviewSourceColumnCommandInput,
  ReviewSourceColumnCommandOutput,
} from "./commands/ReviewSourceColumnCommand";
import type {
  ReviewSourceTableCommandInput,
  ReviewSourceTableCommandOutput,
} from "./commands/ReviewSourceTableCommand";
import type { RollbackOntologyCommandInput, RollbackOntologyCommandOutput } from "./commands/RollbackOntologyCommand";
import type { RunValidationCommandInput, RunValidationCommandOutput } from "./commands/RunValidationCommand";
import type { SearchEmbeddingsCommandInput, SearchEmbeddingsCommandOutput } from "./commands/SearchEmbeddingsCommand";
import type { StartInductionCommandInput, StartInductionCommandOutput } from "./commands/StartInductionCommand";
import type {
  StartOntologyValidationCommandInput,
  StartOntologyValidationCommandOutput,
} from "./commands/StartOntologyValidationCommand";
import type {
  UndoFactConflictResolutionCommandInput,
  UndoFactConflictResolutionCommandOutput,
} from "./commands/UndoFactConflictResolutionCommand";
import type { UpdateMetricCommandInput, UpdateMetricCommandOutput } from "./commands/UpdateMetricCommand";
import type { UpdateNamespaceCommandInput, UpdateNamespaceCommandOutput } from "./commands/UpdateNamespaceCommand";
import type {
  UpdateNamespaceStatusCommandInput,
  UpdateNamespaceStatusCommandOutput,
} from "./commands/UpdateNamespaceStatusCommand";
import type { UpdateProposalCommandInput, UpdateProposalCommandOutput } from "./commands/UpdateProposalCommand";
import type {
  UpdateSourceColumnMetadataCommandInput,
  UpdateSourceColumnMetadataCommandOutput,
} from "./commands/UpdateSourceColumnMetadataCommand";
import type {
  UpdateSourceMetadataCommandInput,
  UpdateSourceMetadataCommandOutput,
} from "./commands/UpdateSourceMetadataCommand";
import type {
  UpdateSourceTableKeysCommandInput,
  UpdateSourceTableKeysCommandOutput,
} from "./commands/UpdateSourceTableKeysCommand";
import type {
  UpdateSourceTableMetadataCommandInput,
  UpdateSourceTableMetadataCommandOutput,
} from "./commands/UpdateSourceTableMetadataCommand";
import type { UploadDocumentCommandInput, UploadDocumentCommandOutput } from "./commands/UploadDocumentCommand";
import type { UploadOntologyCommandInput, UploadOntologyCommandOutput } from "./commands/UploadOntologyCommand";
import type { ValidateMetricCommandInput, ValidateMetricCommandOutput } from "./commands/ValidateMetricCommand";
import type { ValidateProposalCommandInput, ValidateProposalCommandOutput } from "./commands/ValidateProposalCommand";
import type { VerifyOntologyCommandInput, VerifyOntologyCommandOutput } from "./commands/VerifyOntologyCommand";
import {
  type ClientInputEndpointParameters,
  type ClientResolvedEndpointParameters,
  type EndpointParameters,
  resolveClientEndpointParameters,
} from "./endpoint/EndpointParameters";
import { getRuntimeConfig as __getRuntimeConfig } from "./runtimeConfig";
import { type RuntimeExtension, type RuntimeExtensionsConfig, resolveRuntimeExtensions } from "./runtimeExtensions";

export { __Client };

/**
 * @public
 */
export type ServiceInputTypes =
  | AcceptProposalCommandInput
  | ApproveFactCandidateCommandInput
  | ApproveSourceCommandInput
  | AssertFactCommandInput
  | BatchKeepFactConflictsCommandInput
  | BrowseOntologyTreeCommandInput
  | BulkDeleteMetricsCommandInput
  | CancelProposalCommandInput
  | CompileConstraintsCommandInput
  | CreateGrantCommandInput
  | CreateMetricCommandInput
  | CreateNamespaceCommandInput
  | CreatePlatformGrantCommandInput
  | CreateSourceCommandInput
  | DeleteGrantCommandInput
  | DeleteMetricCommandInput
  | DeleteNamespaceCommandInput
  | DeleteOntologyCommandInput
  | DeletePlatformGrantCommandInput
  | DeleteSourceCommandInput
  | DiffOntologyVersionsCommandInput
  | DownloadOntologyCommandInput
  | ExportOntologyBundleCommandInput
  | ExportOntologyVersionCommandInput
  | ExportOsiCommandInput
  | FetchOntologyCommandInput
  | FindGraphPathCommandInput
  | FindLinksCommandInput
  | GetAnswerQualityCommandInput
  | GetCanvasManifestCommandInput
  | GetCanvasSubgraphCommandInput
  | GetDictionaryCommandInput
  | GetDictionaryCommentCoverageCommandInput
  | GetDictionaryViewCommandInput
  | GetEntityCommandInput
  | GetEntityEmbeddingsCommandInput
  | GetEntityProvenanceCommandInput
  | GetFactCommandInput
  | GetGraphClassCommandInput
  | GetGraphDatatypePropertyCommandInput
  | GetGraphObjectPropertyCommandInput
  | GetImportJobCommandInput
  | GetInductionJobCommandInput
  | GetInferConstraintsJobCommandInput
  | GetIngestStatusCommandInput
  | GetIngestionRunCommandInput
  | GetMetricCardCommandInput
  | GetMetricCommandInput
  | GetMetricFamilyCommandInput
  | GetMetricReportManifestCommandInput
  | GetNamespaceCommandInput
  | GetNamespaceRoleCommandInput
  | GetOntologyCommandInput
  | GetOntologyDiffCommandInput
  | GetOntologyOverviewCommandInput
  | GetOntologySnapshotCommandInput
  | GetOntologyUploadUrlCommandInput
  | GetOntologyValidationJobCommandInput
  | GetOntologyVersionCommandInput
  | GetOntologyVersionProposalCommandInput
  | GetOsiUploadUrlCommandInput
  | GetProposalCommandInput
  | GetProposalUploadUrlsCommandInput
  | GetProposalValidationJobCommandInput
  | GetReasoningStatusCommandInput
  | GetSourceCommandInput
  | GetSourceScanJobCommandInput
  | GetSourceTableCommandInput
  | GetSourceUploadUrlsCommandInput
  | GetSystemHealthCommandInput
  | GraphSearchCommandInput
  | HealthCheckCommandInput
  | ImportBundleCommandInput
  | ImportOntologyCommandInput
  | ImportOsiCommandInput
  | InferConstraintsCommandInput
  | IngestOntologyFromS3CommandInput
  | InspectOntologyBundleCommandInput
  | KeepRescanRemovalCommandInput
  | ListAnswerQualityRunsCommandInput
  | ListDictionariesCommandInput
  | ListDocumentChunksCommandInput
  | ListDocumentsCommandInput
  | ListFactCandidatesCommandInput
  | ListFactConflictsCommandInput
  | ListFactEventsCommandInput
  | ListFactsCommandInput
  | ListFoundationalOntologiesCommandInput
  | ListInducedDatasourcesCommandInput
  | ListInductionJobsCommandInput
  | ListIngestionRunsCommandInput
  | ListMetricsCommandInput
  | ListNamespaceGrantsCommandInput
  | ListNamespaceRolesCommandInput
  | ListNamespacesCommandInput
  | ListOntologiesCommandInput
  | ListOntologyEventsCommandInput
  | ListOntologyInstancesCommandInput
  | ListOntologyProposalsCommandInput
  | ListOntologyVersionsCommandInput
  | ListPlatformGrantsCommandInput
  | ListPlatformRolesCommandInput
  | ListPrincipalGrantsCommandInput
  | ListProposalsCommandInput
  | ListSourceScanJobsCommandInput
  | ListSourceTablesCommandInput
  | ListSourcesCommandInput
  | ListStatementsCommandInput
  | ListTermsCommandInput
  | LoadFoundationalOntologyCommandInput
  | MaterializeReasoningCommandInput
  | ProposeOntologyVersionCommandInput
  | PublishOntologyCommandInput
  | PutSourceEventRescanCommandInput
  | PutSourceRescanScheduleCommandInput
  | RefreshDictionariesCommandInput
  | RejectFactCandidateCommandInput
  | RejectProposalsCommandInput
  | RejectSourceCommandInput
  | RepairProposalDatatypesCommandInput
  | RescanSourceCommandInput
  | ResolveFactConflictsCommandInput
  | RestoreFactCommandInput
  | RetractFactCommandInput
  | RetractFactsCommandInput
  | ReviewOntologyProposalCommandInput
  | ReviewSourceColumnCommandInput
  | ReviewSourceTableCommandInput
  | RollbackOntologyCommandInput
  | RunValidationCommandInput
  | SearchEmbeddingsCommandInput
  | StartInductionCommandInput
  | StartOntologyValidationCommandInput
  | UndoFactConflictResolutionCommandInput
  | UpdateMetricCommandInput
  | UpdateNamespaceCommandInput
  | UpdateNamespaceStatusCommandInput
  | UpdateProposalCommandInput
  | UpdateSourceColumnMetadataCommandInput
  | UpdateSourceMetadataCommandInput
  | UpdateSourceTableKeysCommandInput
  | UpdateSourceTableMetadataCommandInput
  | UploadDocumentCommandInput
  | UploadOntologyCommandInput
  | ValidateMetricCommandInput
  | ValidateProposalCommandInput
  | VerifyOntologyCommandInput;

/**
 * @public
 */
export type ServiceOutputTypes =
  | AcceptProposalCommandOutput
  | ApproveFactCandidateCommandOutput
  | ApproveSourceCommandOutput
  | AssertFactCommandOutput
  | BatchKeepFactConflictsCommandOutput
  | BrowseOntologyTreeCommandOutput
  | BulkDeleteMetricsCommandOutput
  | CancelProposalCommandOutput
  | CompileConstraintsCommandOutput
  | CreateGrantCommandOutput
  | CreateMetricCommandOutput
  | CreateNamespaceCommandOutput
  | CreatePlatformGrantCommandOutput
  | CreateSourceCommandOutput
  | DeleteGrantCommandOutput
  | DeleteMetricCommandOutput
  | DeleteNamespaceCommandOutput
  | DeleteOntologyCommandOutput
  | DeletePlatformGrantCommandOutput
  | DeleteSourceCommandOutput
  | DiffOntologyVersionsCommandOutput
  | DownloadOntologyCommandOutput
  | ExportOntologyBundleCommandOutput
  | ExportOntologyVersionCommandOutput
  | ExportOsiCommandOutput
  | FetchOntologyCommandOutput
  | FindGraphPathCommandOutput
  | FindLinksCommandOutput
  | GetAnswerQualityCommandOutput
  | GetCanvasManifestCommandOutput
  | GetCanvasSubgraphCommandOutput
  | GetDictionaryCommandOutput
  | GetDictionaryCommentCoverageCommandOutput
  | GetDictionaryViewCommandOutput
  | GetEntityCommandOutput
  | GetEntityEmbeddingsCommandOutput
  | GetEntityProvenanceCommandOutput
  | GetFactCommandOutput
  | GetGraphClassCommandOutput
  | GetGraphDatatypePropertyCommandOutput
  | GetGraphObjectPropertyCommandOutput
  | GetImportJobCommandOutput
  | GetInductionJobCommandOutput
  | GetInferConstraintsJobCommandOutput
  | GetIngestStatusCommandOutput
  | GetIngestionRunCommandOutput
  | GetMetricCardCommandOutput
  | GetMetricCommandOutput
  | GetMetricFamilyCommandOutput
  | GetMetricReportManifestCommandOutput
  | GetNamespaceCommandOutput
  | GetNamespaceRoleCommandOutput
  | GetOntologyCommandOutput
  | GetOntologyDiffCommandOutput
  | GetOntologyOverviewCommandOutput
  | GetOntologySnapshotCommandOutput
  | GetOntologyUploadUrlCommandOutput
  | GetOntologyValidationJobCommandOutput
  | GetOntologyVersionCommandOutput
  | GetOntologyVersionProposalCommandOutput
  | GetOsiUploadUrlCommandOutput
  | GetProposalCommandOutput
  | GetProposalUploadUrlsCommandOutput
  | GetProposalValidationJobCommandOutput
  | GetReasoningStatusCommandOutput
  | GetSourceCommandOutput
  | GetSourceScanJobCommandOutput
  | GetSourceTableCommandOutput
  | GetSourceUploadUrlsCommandOutput
  | GetSystemHealthCommandOutput
  | GraphSearchCommandOutput
  | HealthCheckCommandOutput
  | ImportBundleCommandOutput
  | ImportOntologyCommandOutput
  | ImportOsiCommandOutput
  | InferConstraintsCommandOutput
  | IngestOntologyFromS3CommandOutput
  | InspectOntologyBundleCommandOutput
  | KeepRescanRemovalCommandOutput
  | ListAnswerQualityRunsCommandOutput
  | ListDictionariesCommandOutput
  | ListDocumentChunksCommandOutput
  | ListDocumentsCommandOutput
  | ListFactCandidatesCommandOutput
  | ListFactConflictsCommandOutput
  | ListFactEventsCommandOutput
  | ListFactsCommandOutput
  | ListFoundationalOntologiesCommandOutput
  | ListInducedDatasourcesCommandOutput
  | ListInductionJobsCommandOutput
  | ListIngestionRunsCommandOutput
  | ListMetricsCommandOutput
  | ListNamespaceGrantsCommandOutput
  | ListNamespaceRolesCommandOutput
  | ListNamespacesCommandOutput
  | ListOntologiesCommandOutput
  | ListOntologyEventsCommandOutput
  | ListOntologyInstancesCommandOutput
  | ListOntologyProposalsCommandOutput
  | ListOntologyVersionsCommandOutput
  | ListPlatformGrantsCommandOutput
  | ListPlatformRolesCommandOutput
  | ListPrincipalGrantsCommandOutput
  | ListProposalsCommandOutput
  | ListSourceScanJobsCommandOutput
  | ListSourceTablesCommandOutput
  | ListSourcesCommandOutput
  | ListStatementsCommandOutput
  | ListTermsCommandOutput
  | LoadFoundationalOntologyCommandOutput
  | MaterializeReasoningCommandOutput
  | ProposeOntologyVersionCommandOutput
  | PublishOntologyCommandOutput
  | PutSourceEventRescanCommandOutput
  | PutSourceRescanScheduleCommandOutput
  | RefreshDictionariesCommandOutput
  | RejectFactCandidateCommandOutput
  | RejectProposalsCommandOutput
  | RejectSourceCommandOutput
  | RepairProposalDatatypesCommandOutput
  | RescanSourceCommandOutput
  | ResolveFactConflictsCommandOutput
  | RestoreFactCommandOutput
  | RetractFactCommandOutput
  | RetractFactsCommandOutput
  | ReviewOntologyProposalCommandOutput
  | ReviewSourceColumnCommandOutput
  | ReviewSourceTableCommandOutput
  | RollbackOntologyCommandOutput
  | RunValidationCommandOutput
  | SearchEmbeddingsCommandOutput
  | StartInductionCommandOutput
  | StartOntologyValidationCommandOutput
  | UndoFactConflictResolutionCommandOutput
  | UpdateMetricCommandOutput
  | UpdateNamespaceCommandOutput
  | UpdateNamespaceStatusCommandOutput
  | UpdateProposalCommandOutput
  | UpdateSourceColumnMetadataCommandOutput
  | UpdateSourceMetadataCommandOutput
  | UpdateSourceTableKeysCommandOutput
  | UpdateSourceTableMetadataCommandOutput
  | UploadDocumentCommandOutput
  | UploadOntologyCommandOutput
  | ValidateMetricCommandOutput
  | ValidateProposalCommandOutput
  | VerifyOntologyCommandOutput;

/**
 * @public
 */
export interface ClientDefaults extends Partial<__SmithyConfiguration<__HttpHandlerOptions>> {
  /**
   * The HTTP handler to use or its constructor options. Fetch in browser and Https in Nodejs.
   */
  requestHandler?: __HttpHandlerUserInput;

  /**
   * A constructor for a class implementing the {@link @smithy/types#ChecksumConstructor} interface
   * that computes the SHA-256 HMAC or checksum of a string or binary buffer.
   * @internal
   */
  sha256?: __ChecksumConstructor | __HashConstructor;

  /**
   * The function that will be used to convert strings into HTTP endpoints.
   * @internal
   */
  urlParser?: __UrlParser;

  /**
   * A function that can calculate the length of a request body.
   * @internal
   */
  bodyLengthChecker?: __BodyLengthCalculator;

  /**
   * A function that converts a stream into an array of bytes.
   * @internal
   */
  streamCollector?: __StreamCollector;

  /**
   * The function that will be used to convert a base64-encoded string to a byte array.
   * @internal
   */
  base64Decoder?: __Decoder;

  /**
   * The function that will be used to convert binary data to a base64-encoded string.
   * @internal
   */
  base64Encoder?: __Encoder;

  /**
   * The function that will be used to convert a UTF8-encoded string to a byte array.
   * @internal
   */
  utf8Decoder?: __Decoder;

  /**
   * The function that will be used to convert binary data to a UTF-8 encoded string.
   * @internal
   */
  utf8Encoder?: __Encoder;

  /**
   * The runtime environment.
   * @internal
   */
  runtime?: string;

  /**
   * Disable dynamically changing the endpoint of the client based on the hostPrefix
   * trait of an operation.
   */
  disableHostPrefix?: boolean;

  /**
   * Setting a client profile is similar to setting a value for the
   * AWS_PROFILE environment variable. Setting a profile on a client
   * in code only affects the single client instance, unlike AWS_PROFILE.
   *
   * When set, and only for environments where an AWS configuration
   * file exists, fields configurable by this file will be retrieved
   * from the specified profile within that file.
   * Conflicting code configuration and environment variables will
   * still have higher priority.
   *
   * For client credential resolution that involves checking the AWS
   * configuration file, the client's profile (this value) will be
   * used unless a different profile is set in the credential
   * provider options.
   *
   */
  profile?: string;

  /**
   * The provider populating default tracking information to be sent with `user-agent`, `x-amz-user-agent` header
   * @internal
   */
  defaultUserAgentProvider?: __Provider<__UserAgent>;

  /**
   * Value for how many times a request will be made at most in case of retry.
   */
  maxAttempts?: number | __Provider<number>;

  /**
   * Specifies which retry algorithm to use.
   * @see https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/Package/-smithy-util-retry/Enum/RETRY_MODES/
   *
   */
  retryMode?: string | __Provider<string>;

  /**
   * Optional logger for logging debug/info/warn/error.
   */
  logger?: __Logger;

  /**
   * Optional extensions
   */
  extensions?: RuntimeExtension[];

  /**
   * The {@link @smithy/smithy-client#DefaultsMode} that will be used to determine how certain default configuration options are resolved in the SDK.
   */
  defaultsMode?: __DefaultsMode | __Provider<__DefaultsMode>;
}

/**
 * @public
 */
export type ControlPlaneServiceClientConfigType = Partial<__SmithyConfiguration<__HttpHandlerOptions>> &
  ClientDefaults &
  UserAgentInputConfig &
  RetryInputConfig &
  HostHeaderInputConfig &
  EndpointInputConfig<EndpointParameters> &
  EndpointRequiredInputConfig &
  HttpAuthSchemeInputConfig &
  ClientInputEndpointParameters;
/**
 * @public
 *
 *  The configuration interface of ControlPlaneServiceClient class constructor that set the region, credentials and other options.
 */
export interface ControlPlaneServiceClientConfig extends ControlPlaneServiceClientConfigType {}

/**
 * @public
 */
export type ControlPlaneServiceClientResolvedConfigType = __SmithyResolvedConfiguration<__HttpHandlerOptions> &
  Required<ClientDefaults> &
  RuntimeExtensionsConfig &
  UserAgentResolvedConfig &
  RetryResolvedConfig &
  HostHeaderResolvedConfig &
  EndpointResolvedConfig<EndpointParameters> &
  EndpointRequiredResolvedConfig &
  HttpAuthSchemeResolvedConfig &
  ClientResolvedEndpointParameters;
/**
 * @public
 *
 *  The resolved configuration interface of ControlPlaneServiceClient class. This is resolved and normalized from the {@link ControlPlaneServiceClientConfig | constructor configuration interface}.
 */
export interface ControlPlaneServiceClientResolvedConfig extends ControlPlaneServiceClientResolvedConfigType {}

/**
 * @public
 */
export class ControlPlaneServiceClient extends __Client<
  __HttpHandlerOptions,
  ServiceInputTypes,
  ServiceOutputTypes,
  ControlPlaneServiceClientResolvedConfig
> {
  /**
   * The resolved configuration of ControlPlaneServiceClient class. This is resolved and normalized from the {@link ControlPlaneServiceClientConfig | constructor configuration interface}.
   */
  readonly config: ControlPlaneServiceClientResolvedConfig;

  constructor(...[configuration]: __CheckOptionalClientConfig<ControlPlaneServiceClientConfig>) {
    const _config_0 = __getRuntimeConfig(configuration || {});
    super(_config_0 as any);
    this.initConfig = _config_0;
    const _config_1 = resolveClientEndpointParameters(_config_0);
    const _config_2 = resolveUserAgentConfig(_config_1);
    const _config_3 = resolveRetryConfig(_config_2);
    const _config_4 = resolveHostHeaderConfig(_config_3);
    const _config_5 = resolveEndpointConfig(_config_4);
    const _config_6 = resolveEndpointRequiredConfig(_config_5);
    const _config_7 = resolveHttpAuthSchemeConfig(_config_6);
    const _config_8 = resolveRuntimeExtensions(_config_7, configuration?.extensions || []);
    this.config = _config_8;
    this.middlewareStack.use(getSchemaSerdePlugin(this.config));
    this.middlewareStack.use(getUserAgentPlugin(this.config));
    this.middlewareStack.use(getRetryPlugin(this.config));
    this.middlewareStack.use(getContentLengthPlugin(this.config));
    this.middlewareStack.use(getHostHeaderPlugin(this.config));
    this.middlewareStack.use(getLoggerPlugin(this.config));
    this.middlewareStack.use(getRecursionDetectionPlugin(this.config));
    this.middlewareStack.use(
      getHttpAuthSchemeEndpointRuleSetPlugin(this.config, {
        httpAuthSchemeParametersProvider: defaultControlPlaneServiceHttpAuthSchemeParametersProvider,
        identityProviderConfigProvider: async (config: ControlPlaneServiceClientResolvedConfig) =>
          new DefaultIdentityProviderConfig({
            "smithy.api#httpBearerAuth": config.token,
          }),
      })
    );
    this.middlewareStack.use(getHttpSigningPlugin(this.config));
  }

  /**
   * Destroy underlying resources, like sockets. It's usually not necessary to do this.
   * However in Node.js, it's best to explicitly shut down the client's agent when it is no longer needed.
   * Otherwise, sockets might stay open for quite a long time before the server terminates them.
   */
  destroy(): void {
    super.destroy();
  }
}
