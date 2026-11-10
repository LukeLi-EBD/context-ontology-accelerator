// smithy-typescript generated code
import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { Command as $Command } from "@smithy/smithy-client";
import type { MetadataBearer as __MetadataBearer } from "@smithy/types";

import type {
  ControlPlaneServiceClientResolvedConfig,
  ServiceInputTypes,
  ServiceOutputTypes,
} from "../ControlPlaneServiceClient";
import { commonParams } from "../endpoint/EndpointParameters";
import type { ListSourceScanJobsInput, ListSourceScanJobsOutput } from "../models/models_1";
import { ListSourceScanJobs$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListSourceScanJobsCommand}.
 */
export interface ListSourceScanJobsCommandInput extends ListSourceScanJobsInput {}
/**
 * @public
 *
 * The output of {@link ListSourceScanJobsCommand}.
 */
export interface ListSourceScanJobsCommandOutput extends ListSourceScanJobsOutput, __MetadataBearer {}

/**
 * List the scan and review history for a DATABASE source, newest first.
 * Combines discovery/enrichment scan rows with steward approve/reject events
 * so the console can show a real audit trail instead of a derived guess.
 *
 * Paginated: a request without `nextToken` returns the newest page; follow
 * `nextToken` until it is absent to read the whole history.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListSourceScanJobsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListSourceScanJobsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListSourceScanJobsInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListSourceScanJobsCommand(input);
 * const response = await client.send(command);
 * // { // ListSourceScanJobsOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // ScanJobEntryList // required
 * //     { // ScanJobEntry
 * //       at: new Date("TIMESTAMP"), // required
 * //       eventType: "SCAN" || "REVIEW",
 * //       status: "STRING_VALUE",
 * //       scanType: "STRING_VALUE",
 * //       triggerType: "INITIAL" || "MANUAL" || "SCHEDULED" || "EVENT",
 * //       tablesDiscovered: Number("int"),
 * //       tablesApproved: Number("int"),
 * //       completedAt: new Date("TIMESTAMP"),
 * //       errorMessage: "STRING_VALUE",
 * //       decision: "APPROVED" || "REJECTED",
 * //       isRescan: true || false,
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListSourceScanJobsCommandInput - {@link ListSourceScanJobsCommandInput}
 * @returns {@link ListSourceScanJobsCommandOutput}
 * @see {@link ListSourceScanJobsCommandInput} for command's `input` shape.
 * @see {@link ListSourceScanJobsCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link InternalServerError} (server fault)
 *  Returned with HTTP 500 when the service fails unexpectedly. The message is a
 * fixed, generic description; the underlying cause is logged, never returned.
 *
 * @throws {@link ServiceUnavailableError} (server fault)
 *  Returned with HTTP 503 when the service, or a required dependency (including
 * one it needs to handle the request safely), is temporarily unavailable. For
 * example, a create that
 * carries a `clientToken` fails closed with this error when the retry-safety
 * store cannot be reached, rather than risk running the create twice. Retry
 * the request (with the same `clientToken`) after a backoff.
 *
 * @throws {@link ControlPlaneServiceServiceException}
 * <p>Base exception class for all service exceptions from ControlPlaneService service.</p>
 *
 *
 * @example List a source's scan and review history, newest first
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new ListSourceScanJobsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       at: "2026-07-23T15:02:00Z",
 *       decision: "APPROVED",
 *       eventType: "REVIEW",
 *       isRescan: false,
 *       status: "APPROVED",
 *       tablesApproved: 12
 *     },
 *     {
 *       at: "2026-07-23T14:30:00Z",
 *       completedAt: "2026-07-23T14:35:00Z",
 *       eventType: "SCAN",
 *       scanType: "full",
 *       status: "COMPLETED",
 *       tablesDiscovered: 12
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @example Page through a long history
 * ```javascript
 * //
 * const input = {
 *   maxResults: 1,
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new ListSourceScanJobsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       at: "2026-07-23T15:02:00Z",
 *       decision: "APPROVED",
 *       eventType: "REVIEW",
 *       isRescan: false,
 *       status: "APPROVED",
 *       tablesApproved: 12
 *     }
 *   ],
 *   nextToken: "eyJTSyI6ICIyMDI2LTA3LTIzVDE1OjAyOjAwWiJ9"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListSourceScanJobsCommand extends $Command
  .classBuilder<
    ListSourceScanJobsCommandInput,
    ListSourceScanJobsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListSourceScanJobs", {})
  .n("ControlPlaneServiceClient", "ListSourceScanJobsCommand")
  .sc(ListSourceScanJobs$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListSourceScanJobsInput;
      output: ListSourceScanJobsOutput;
    };
    sdk: {
      input: ListSourceScanJobsCommandInput;
      output: ListSourceScanJobsCommandOutput;
    };
  };
}
