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
import type { ListFactCandidatesInput, ListFactCandidatesOutput } from "../models/models_0";
import { ListFactCandidates$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListFactCandidatesCommand}.
 */
export interface ListFactCandidatesCommandInput extends ListFactCandidatesInput {}
/**
 * @public
 *
 * The output of {@link ListFactCandidatesCommand}.
 */
export interface ListFactCandidatesCommandOutput extends ListFactCandidatesOutput, __MetadataBearer {}

/**
 * List extracted fact candidates awaiting review (or filtered by status).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListFactCandidatesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListFactCandidatesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListFactCandidatesInput
 *   namespaceId: "STRING_VALUE", // required
 *   documentId: "STRING_VALUE",
 *   status: "PENDING" || "APPROVED" || "REJECTED",
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListFactCandidatesCommand(input);
 * const response = await client.send(command);
 * // { // ListFactCandidatesOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // FactCandidateList // required
 * //     { // FactCandidate
 * //       candidateId: "STRING_VALUE", // required
 * //       subject: "STRING_VALUE", // required
 * //       predicate: "STRING_VALUE", // required
 * //       object: "STRING_VALUE", // required
 * //       confidence: Number("float"), // required
 * //       status: "PENDING" || "APPROVED" || "REJECTED", // required
 * //       documentId: "STRING_VALUE",
 * //       chunkId: "STRING_VALUE",
 * //       evidence: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListFactCandidatesCommandInput - {@link ListFactCandidatesCommandInput}
 * @returns {@link ListFactCandidatesCommandOutput}
 * @see {@link ListFactCandidatesCommandInput} for command's `input` shape.
 * @see {@link ListFactCandidatesCommandOutput} for command's `response` shape.
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
 * @example List pending candidates
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11",
 *   status: "PENDING"
 * };
 * const command = new ListFactCandidatesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items:   []
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListFactCandidatesCommand extends $Command
  .classBuilder<
    ListFactCandidatesCommandInput,
    ListFactCandidatesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListFactCandidates", {})
  .n("ControlPlaneServiceClient", "ListFactCandidatesCommand")
  .sc(ListFactCandidates$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListFactCandidatesInput;
      output: ListFactCandidatesOutput;
    };
    sdk: {
      input: ListFactCandidatesCommandInput;
      output: ListFactCandidatesCommandOutput;
    };
  };
}
