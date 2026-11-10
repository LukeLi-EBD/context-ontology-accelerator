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
import type { RefreshDictionariesInput, RefreshDictionariesOutput } from "../models/models_0";
import { RefreshDictionaries$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RefreshDictionariesCommand}.
 */
export interface RefreshDictionariesCommandInput extends RefreshDictionariesInput {}
/**
 * @public
 *
 * The output of {@link RefreshDictionariesCommand}.
 */
export interface RefreshDictionariesCommandOutput extends RefreshDictionariesOutput, __MetadataBearer {}

/**
 * Introspect a source and replace its dictionary snapshot.
 *
 * A repeated `idempotencyKey` for a succeeded run returns that run instead of
 * introspecting again. A still-running duplicate is a conflict. Columns whose
 * stored `binding_method` is `manual` are never overwritten.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RefreshDictionariesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RefreshDictionariesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RefreshDictionariesInput
 *   namespaceId: "STRING_VALUE", // required
 *   sourceId: "STRING_VALUE", // required
 *   idempotencyKey: "STRING_VALUE",
 *   requestedBy: "STRING_VALUE",
 * };
 * const command = new RefreshDictionariesCommand(input);
 * const response = await client.send(command);
 * // { // RefreshDictionariesOutput
 * //   run: { // DictionaryRefreshRun
 * //     runId: "STRING_VALUE", // required
 * //     sourceId: "STRING_VALUE", // required
 * //     status: "STRING_VALUE", // required
 * //     idempotencyKey: "STRING_VALUE",
 * //     requestedBy: "STRING_VALUE",
 * //     startedAt: "STRING_VALUE",
 * //     finishedAt: "STRING_VALUE",
 * //     processed: Number("int"),
 * //     inserted: Number("int"),
 * //     updated: Number("int"),
 * //     unchanged: Number("int"),
 * //     removed: Number("int"),
 * //     error: "STRING_VALUE",
 * //   },
 * //   bindingBasis: "STRING_VALUE", // required
 * //   warnings: [ // StringList
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param RefreshDictionariesCommandInput - {@link RefreshDictionariesCommandInput}
 * @returns {@link RefreshDictionariesCommandOutput}
 * @see {@link RefreshDictionariesCommandInput} for command's `input` shape.
 * @see {@link RefreshDictionariesCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link ValidationError} (client fault)
 *  Standard error structure
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Refresh a source's dictionary (idempotent retry)
 * ```javascript
 * //
 * const input = {
 *   idempotencyKey: "refresh-20261110-0915",
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   requestedBy: "data-team@example.com",
 *   sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d"
 * };
 * const command = new RefreshDictionariesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   bindingBasis: "published-ontology",
 *   run: {
 *     finishedAt: "2026-11-10T09:15:02Z",
 *     idempotencyKey: "refresh-20261110-0915",
 *     inserted: 2,
 *     processed: 143,
 *     removed: 0,
 *     requestedBy: "data-team@example.com",
 *     runId: "5c1e7a90-2b4f-4d8a-a1c3-7e9f0b2d4c68",
 *     sourceId: "3f8b9c2e-1a4d-4e7b-9c5d-2a6b8e0f1c3d",
 *     startedAt: "2026-11-10T09:15:00Z",
 *     status: "succeeded",
 *     unchanged: 136,
 *     updated: 5
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RefreshDictionariesCommand extends $Command
  .classBuilder<
    RefreshDictionariesCommandInput,
    RefreshDictionariesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RefreshDictionaries", {})
  .n("ControlPlaneServiceClient", "RefreshDictionariesCommand")
  .sc(RefreshDictionaries$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RefreshDictionariesInput;
      output: RefreshDictionariesOutput;
    };
    sdk: {
      input: RefreshDictionariesCommandInput;
      output: RefreshDictionariesCommandOutput;
    };
  };
}
