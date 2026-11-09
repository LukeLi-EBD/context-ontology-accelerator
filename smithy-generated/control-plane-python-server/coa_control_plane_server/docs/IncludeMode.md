# IncludeMode

Opt-in expansion for `GetInductionJob`. Omitting it returns the slim poll shape: every scalar count, `status`, `proposalId`/`duplicateOf` and `error` are preserved, but `report.matches` is returned empty so the response stays under the API's 6MB response cap (at 50k tables the full match list holds ~836k entries and makes a completed job unpollable). Per-match detail is persisted on the proposal and read via the proposal endpoints.

## Enum

* `REPORT` (value: `'report'`)

* `FULL` (value: `'full'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


