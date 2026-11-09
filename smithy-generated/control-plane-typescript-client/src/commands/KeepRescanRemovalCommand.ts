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
import type { KeepRescanRemovalInput, KeepRescanRemovalOutput } from "../models/models_0";
import { KeepRescanRemoval$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link KeepRescanRemovalCommand}.
 */
export interface KeepRescanRemovalCommandInput extends KeepRescanRemovalInput {}
/**
 * @public
 *
 * The output of {@link KeepRescanRemovalCommand}.
 */
export interface KeepRescanRemovalCommandOutput extends KeepRescanRemovalOutput, __MetadataBearer {}

/**
 * Decline a re-scan-flagged removal so approving the re-scan will NOT delete
 * it. Drops the table (or one column of it) from the re-scan removal set in the
 * backup blob; the surfaced pendingDeletion marker clears on the next read.
 *
 * "Removed from the source" does not always mean "deleted" — a partial scan, a
 * permission change, or a narrowed include/exclude filter can drop a table or
 * column that should be kept. This lets the steward veto a specific removal.
 *
 * Only valid while the source is in RESCAN_REVIEW. Omit columnName to keep the
 * whole table; set it to keep one removed column. Idempotent — keeping an item
 * that is not in the removal set is a no-op.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, KeepRescanRemovalCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, KeepRescanRemovalCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // KeepRescanRemovalInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   tableId: "STRING_VALUE", // required
 *   columnName: "STRING_VALUE",
 * };
 * const command = new KeepRescanRemovalCommand(input);
 * const response = await client.send(command);
 * // { // KeepRescanRemovalOutput
 * //   tableId: "STRING_VALUE", // required
 * //   columnName: "STRING_VALUE",
 * //   pendingDeletion: true || false, // required
 * // };
 *
 * ```
 *
 * @param KeepRescanRemovalCommandInput - {@link KeepRescanRemovalCommandInput}
 * @returns {@link KeepRescanRemovalCommandOutput}
 * @see {@link KeepRescanRemovalCommandInput} for command's `input` shape.
 * @see {@link KeepRescanRemovalCommandOutput} for command's `response` shape.
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
 * @example Keep a table the re-scan flagged as removed
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.legacy_orders"
 * };
 * const command = new KeepRescanRemovalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   pendingDeletion: false,
 *   tableId: "sales.legacy_orders"
 * }
 * *\/
 * ```
 *
 * @example Keep a single column the re-scan flagged as removed
 * ```javascript
 * //
 * const input = {
 *   columnName: "legacy_region_code",
 *   namespaceId: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
 *   sourceId: "src-7f3a9c1e",
 *   tableId: "sales.orders"
 * };
 * const command = new KeepRescanRemovalCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   columnName: "legacy_region_code",
 *   pendingDeletion: false,
 *   tableId: "sales.orders"
 * }
 * *\/
 * ```
 *
 * @public
 */
export class KeepRescanRemovalCommand extends $Command
  .classBuilder<
    KeepRescanRemovalCommandInput,
    KeepRescanRemovalCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "KeepRescanRemoval", {})
  .n("ControlPlaneServiceClient", "KeepRescanRemovalCommand")
  .sc(KeepRescanRemoval$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: KeepRescanRemovalInput;
      output: KeepRescanRemovalOutput;
    };
    sdk: {
      input: KeepRescanRemovalCommandInput;
      output: KeepRescanRemovalCommandOutput;
    };
  };
}
