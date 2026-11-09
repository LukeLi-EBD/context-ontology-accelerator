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
import type { RepairProposalDatatypesInput, RepairProposalDatatypesOutput } from "../models/models_0";
import { RepairProposalDatatypes$ } from "../schemas/schemas_0";

/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link RepairProposalDatatypesCommand}.
 */
export interface RepairProposalDatatypesCommandInput extends RepairProposalDatatypesInput {}
/**
 * @public
 *
 * The output of {@link RepairProposalDatatypesCommand}.
 */
export interface RepairProposalDatatypesCommandOutput extends RepairProposalDatatypesOutput, __MetadataBearer {}

/**
 * Repair malformed / mis-cased / aliased XSD datatype tokens in a proposal's
 * stored Turtle (e.g. `xsd:datetime` → `xsd:dateTime`, `xsd:varchar` →
 * `xsd:string`). User-initiated + consent-gated: the DatatypeTokenValidator
 * surfaces the offending tokens at validation time, and the user invokes this
 * to apply the fix. Server-authoritative (the canonical XSD map lives on the
 * server, not the client). Rewrites known-malformed tokens only — valid types
 * (incl. `xsd:date`) and unrecognized `xsd:` tokens are left untouched.
 *
 * With `dryRun` true, computes and returns the same change list WITHOUT
 * persisting — used by the accept-time guard to detect unrepaired datatype
 * issues before an accept, without mutating the proposal.
 *
 * Naturally idempotent, so there is no `clientToken`: a repeat finds the
 * tokens already canonical and rewrites nothing (`repairedCount` 0).
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { ControlPlaneServiceClient, RepairProposalDatatypesCommand } from "@coa/control-plane-client"; // ES Modules import
 * // const { ControlPlaneServiceClient, RepairProposalDatatypesCommand } = require("@coa/control-plane-client"); // CommonJS import
 * // import type { ControlPlaneServiceClientConfig } from "@coa/control-plane-client";
 * const config = {}; // type is ControlPlaneServiceClientConfig
 * const client = new ControlPlaneServiceClient(config);
 * const input = { // RepairProposalDatatypesInput
 *   namespaceId: "STRING_VALUE", // required
 *   proposalId: "STRING_VALUE", // required
 *   dryRun: true || false,
 * };
 * const command = new RepairProposalDatatypesCommand(input);
 * const response = await client.send(command);
 * // { // RepairProposalDatatypesOutput
 * //   proposalId: "STRING_VALUE", // required
 * //   repairedCount: Number("int"), // required
 * //   changes: [ // DatatypeRepairChangeList // required
 * //     { // DatatypeRepairChange
 * //       found: "STRING_VALUE", // required
 * //       canonical: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   dryRun: true || false,
 * // };
 *
 * ```
 *
 * @param RepairProposalDatatypesCommandInput - {@link RepairProposalDatatypesCommandInput}
 * @returns {@link RepairProposalDatatypesCommandOutput}
 * @see {@link RepairProposalDatatypesCommandInput} for command's `input` shape.
 * @see {@link RepairProposalDatatypesCommandOutput} for command's `response` shape.
 * @see {@link ControlPlaneServiceClientResolvedConfig | config} for ControlPlaneServiceClient's `config` shape.
 *
 * @throws {@link NotFoundError} (client fault)
 *  Returned with HTTP 404 when the requested resource does not exist.
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
 * @example Repair malformed datatype tokens in a proposal
 * ```javascript
 * //
 * const input = {
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new RepairProposalDatatypesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   changes: [
 *     {
 *       canonical: "http://www.w3.org/2001/XMLSchema#integer",
 *       found: "xsd:integar"
 *     }
 *   ],
 *   dryRun: false,
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   repairedCount: 1
 * }
 * *\/
 * ```
 *
 * @example Preview datatype repairs without persisting (dry run)
 * ```javascript
 * //
 * const input = {
 *   dryRun: true,
 *   namespaceId: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e"
 * };
 * const command = new RepairProposalDatatypesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   changes: [
 *     {
 *       canonical: "http://www.w3.org/2001/XMLSchema#integer",
 *       found: "xsd:integar"
 *     }
 *   ],
 *   dryRun: true,
 *   proposalId: "7c2e9a1b-4d6f-4b8a-9e3c-1f0a2b5d7c9e",
 *   repairedCount: 1
 * }
 * *\/
 * ```
 *
 * @public
 */
export class RepairProposalDatatypesCommand extends $Command
  .classBuilder<
    RepairProposalDatatypesCommandInput,
    RepairProposalDatatypesCommandOutput,
    ControlPlaneServiceClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >()
  .ep(commonParams)
  .m(function (this: any, Command: any, cs: any, config: ControlPlaneServiceClientResolvedConfig, o: any) {
    return [getEndpointPlugin(config, Command.getEndpointParameterInstructions())];
  })
  .s("ControlPlaneService", "RepairProposalDatatypes", {})
  .n("ControlPlaneServiceClient", "RepairProposalDatatypesCommand")
  .sc(RepairProposalDatatypes$)
  .build() {
  /** @internal type navigation helper, not in runtime. */
  protected declare static __types: {
    api: {
      input: RepairProposalDatatypesInput;
      output: RepairProposalDatatypesOutput;
    };
    sdk: {
      input: RepairProposalDatatypesCommandInput;
      output: RepairProposalDatatypesCommandOutput;
    };
  };
}
