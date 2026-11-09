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
import type { RescanSourceInput, RescanSourceOutput } from "../models/models_0";
import { RescanSource$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RescanSourceCommand}.
 */
export interface RescanSourceCommandInput extends RescanSourceInput {}
/**
 * @public
 *
 * The output of {@link RescanSourceCommand}.
 */
export interface RescanSourceCommandOutput extends RescanSourceOutput, __MetadataBearer {}

/**
 * Re-trigger the scan/ingestion pipeline for an existing source.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RescanSourceCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RescanSourceCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RescanSourceInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   confirmDiscardOpenReview: true || false,
 *   clientToken: "STRING_VALUE",
 * };
 * const command = new RescanSourceCommand(input);
 * const response = await client.send(command);
 * // { // RescanSourceOutput
 * //   sourceId: "STRING_VALUE",
 * //   status: "REGISTERED" || "SCANNING" || "SCANNING_ENTITY_EXTRACTION" || "SCANNING_KG_BUILD" || "ENRICHING" || "PENDING_REVIEW" || "RESCAN_REVIEW" || "APPROVING" || "APPROVAL_FAILED" || "REJECTING" || "REJECTION_FAILED" || "COMPLETED" || "APPROVED" || "REJECTED" || "SCAN_FAILED" || "DELETING" || "DELETED" || "DELETE_FAILED",
 * // };
 *
 * ```
 *
 * @param RescanSourceCommandInput - {@link RescanSourceCommandInput}
 * @returns {@link RescanSourceCommandOutput}
 * @see {@link RescanSourceCommandInput} for command's `input` shape.
 * @see {@link RescanSourceCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ConflictError} (client fault)
 *  Returned with HTTP 409 when a request conflicts with the current state of the resource, such as a duplicate.
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
 * @example Re-scan an existing source
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new RescanSourceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   sourceId: "src-7f3a9c1e",
 *   status: "SCANNING"
 * }
 * *\/
 * ```
 *
 * @example Re-scan with an idempotency token so a retry starts no second scan
 * ```javascript
 * //
 * const input = {
 *   clientToken: "6f1c2b9e-4d3a-4f0e-9b8a-2c1d0e9f8a7b",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e"
 * };
 * const command = new RescanSourceCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   sourceId: "src-7f3a9c1e",
 *   status: "SCANNING"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RescanSourceCommand extends $Command
  .classBuilder<
    RescanSourceCommandInput,
    RescanSourceCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RescanSource", {})
  .n("ControlPlaneServiceClient", "RescanSourceCommand")
  .sc(RescanSource$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RescanSourceInput;
      output: RescanSourceOutput;
    };
    sdk: {
      input: RescanSourceCommandInput;
      output: RescanSourceCommandOutput;
    };
  };
}
