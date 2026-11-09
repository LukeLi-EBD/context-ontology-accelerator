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
import type { ListDocumentsInput, ListDocumentsOutput } from "../models/models_0";
import { ListDocuments$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListDocumentsCommand}.
 */
export interface ListDocumentsCommandInput extends ListDocumentsInput {}
/**
 * @public
 *
 * The output of {@link ListDocumentsCommand}.
 */
export interface ListDocumentsCommandOutput extends ListDocumentsOutput, __MetadataBearer {}

/**
 * List documents registered in the namespace, newest first.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListDocumentsCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListDocumentsCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListDocumentsInput
 *   namespaceId: "STRING_VALUE", // required
 *   status: "UPLOADED" || "PROCESSING" || "INDEXED" || "FAILED",
 *   nextToken: "STRING_VALUE",
 *   maxResults: Number("int"),
 * };
 * const command = new ListDocumentsCommand(input);
 * const response = await client.send(command);
 * // { // ListDocumentsOutput
 * //   nextToken: "STRING_VALUE",
 * //   items: [ // DocumentSummaryList // required
 * //     { // DocumentSummary
 * //       documentId: "STRING_VALUE", // required
 * //       title: "STRING_VALUE", // required
 * //       status: "UPLOADED" || "PROCESSING" || "INDEXED" || "FAILED", // required
 * //       chunkCount: Number("int"), // required
 * //       updatedAt: "STRING_VALUE", // required
 * //       errorMessage: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListDocumentsCommandInput - {@link ListDocumentsCommandInput}
 * @returns {@link ListDocumentsCommandOutput}
 * @see {@link ListDocumentsCommandInput} for command's `input` shape.
 * @see {@link ListDocumentsCommandOutput} for command's `response` shape.
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
 * @example List the namespace's documents
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "2f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11"
 * };
 * const command = new ListDocumentsCommand(input);
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
export class ListDocumentsCommand extends $Command
  .classBuilder<
    ListDocumentsCommandInput,
    ListDocumentsCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListDocuments", {})
  .n("ControlPlaneServiceClient", "ListDocumentsCommand")
  .sc(ListDocuments$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListDocumentsInput;
      output: ListDocumentsOutput;
    };
    sdk: {
      input: ListDocumentsCommandInput;
      output: ListDocumentsCommandOutput;
    };
  };
}
