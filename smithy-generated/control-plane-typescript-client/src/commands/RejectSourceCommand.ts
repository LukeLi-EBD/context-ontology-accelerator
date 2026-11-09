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
import type { RejectSourceInput, RejectSourceOutput } from "../models/models_0";
import { RejectSource$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RejectSourceCommand}.
 */
export interface RejectSourceCommandInput extends RejectSourceInput {}
/**
 * @public
 *
 * The output of {@link RejectSourceCommand}.
 */
export interface RejectSourceCommandOutput extends RejectSourceOutput, __MetadataBearer {}

/**
 * Reject all PENDING tables and columns of a DATABASE source asynchronously.
 *
 * Returns 202 immediately and transitions the source's status to REJECTING.
 * A background worker writes DataZone asset revisions, marking each
 * non-REJECTED column as REJECTED. On success the source becomes REJECTED,
 * which is terminal (rejecting a re-scan instead restores the pre-rescan
 * state and returns the source to APPROVED). On failure it becomes
 * REJECTION_FAILED. Clients
 * poll the source's status via GetSource until it leaves the REJECTING state.
 *
 * Returns 409 if the source is not in PENDING_REVIEW or REJECTION_FAILED.
 *
 * Takes no clientToken: it is safe to retry as is. The request is a
 * conditional status transition, so a duplicate while the first is in flight
 * (REJECTING) or after it finished (REJECTED, or APPROVED after a re-scan
 * reject) gets 409 and starts no second worker; after REJECTION_FAILED a retry
 * is the intended recovery.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RejectSourceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RejectSourceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RejectSourceInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 * };
 * const command = new RejectSourceCommand(input);
 * const response = await client.send(command);
 * // { // RejectSourceOutput
 * //   sourceId: "STRING_VALUE", // required
 * //   status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED", // required
 * // };
 *
 * ```
 *
 * @param RejectSourceCommandInput - {@link RejectSourceCommandInput}
 * @returns {@link RejectSourceCommandOutput}
 * @see {@link RejectSourceCommandInput} for command's `input` shape.
 * @see {@link RejectSourceCommandOutput} for command's `response` shape.
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
 * @example Bulk-reject all pending tables and columns of a source
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new RejectSourceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   sourceId: "src-7f3a9c1e",
 *   status: "REJECTING"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RejectSourceCommand extends $Command
  .classBuilder<
    RejectSourceCommandInput,
    RejectSourceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RejectSource", {})
  .n("ControlPlaneServiceClient", "RejectSourceCommand")
  .sc(RejectSource$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RejectSourceInput;
      output: RejectSourceOutput;
    };
    sdk: {
      input: RejectSourceCommandInput;
      output: RejectSourceCommandOutput;
    };
  };
}
