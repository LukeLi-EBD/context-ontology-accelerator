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
import type { ListFoundationalOntologiesInput, ListFoundationalOntologiesOutput } from "../models/models_0";
import { ListFoundationalOntologies$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListFoundationalOntologiesCommand}.
 */
export interface ListFoundationalOntologiesCommandInput extends ListFoundationalOntologiesInput {}
/**
 * @public
 *
 * The output of {@link ListFoundationalOntologiesCommand}.
 */
export interface ListFoundationalOntologiesCommandOutput extends ListFoundationalOntologiesOutput, __MetadataBearer {}

/**
 * List the curated catalog of foundational ontologies available for grounding.
 *
 * Not paginated: the catalog is a fixed list compiled into the service (a
 * handful of entries), not data that grows per namespace.
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, ListFoundationalOntologiesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, ListFoundationalOntologiesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // ListFoundationalOntologiesInput
 *   namespaceId: "STRING_VALUE", // required
 * };
 * const command = new ListFoundationalOntologiesCommand(input);
 * const response = await client.send(command);
 * // { // ListFoundationalOntologiesOutput
 * //   items: [ // FoundationalOntologyList // required
 * //     { // FoundationalOntologySummary
 * //       key: "STRING_VALUE", // required
 * //       title: "STRING_VALUE", // required
 * //       description: "STRING_VALUE",
 * //       uri: "STRING_VALUE",
 * //       domainTags: [ // StringList
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListFoundationalOntologiesCommandInput - {@link ListFoundationalOntologiesCommandInput}
 * @returns {@link ListFoundationalOntologiesCommandOutput}
 * @see {@link ListFoundationalOntologiesCommandInput} for command's `input` shape.
 * @see {@link ListFoundationalOntologiesCommandOutput} for command's `response` shape.
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
 * @example List available foundational ontologies
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
 * };
 * const command = new ListFoundationalOntologiesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   items: [
 *     {
 *       description: "Common vocabulary for structured web data",
 *       domainTags: [
 *         "general",
 *         "ecommerce"
 *       ],
 *       key: "schema-org-core",
 *       title: "Schema.org Core",
 *       uri: "https://schema.org/"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export class ListFoundationalOntologiesCommand extends $Command
  .classBuilder<
    ListFoundationalOntologiesCommandInput,
    ListFoundationalOntologiesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "ListFoundationalOntologies", {})
  .n("ControlPlaneServiceClient", "ListFoundationalOntologiesCommand")
  .sc(ListFoundationalOntologies$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: ListFoundationalOntologiesInput;
      output: ListFoundationalOntologiesOutput;
    };
    sdk: {
      input: ListFoundationalOntologiesCommandInput;
      output: ListFoundationalOntologiesCommandOutput;
    };
  };
}
