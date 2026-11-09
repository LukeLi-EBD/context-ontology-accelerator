# ProposalStatus

Proposal status.  ``inducing`` is the FIRST in-flight state: the induction was triggered and a background worker is building the ontology. A stub proposal row is written at trigger time (so the run is visible in the proposals list immediately and survives a browser refresh); the same row is upserted to ``pending`` when the worker finishes, or to ``failed`` if it errors. Clients poll ``ListProposals`` to observe the transition.  ``accepting`` is a later in-flight state: the user submitted ``AcceptProposal`` and a background worker is merging the ontology. It is followed by ``embeddingsSync`` while the just-written embeddings become searchable in the (eventually-consistent) vector index. The status then flips to ``accepted`` on success, or to ``acceptFailed`` with ``acceptError`` naming the pipeline step that failed. An ``acceptFailed`` proposal is re-acceptable — the accept pipeline is idempotent on re-run — so the client may submit ``AcceptProposal`` again once the cause is resolved. Clients poll ``GetProposal`` to observe the transitions.

## Enum

* `INDUCING` (value: `'inducing'`)

* `PENDING` (value: `'pending'`)

* `ACCEPTING` (value: `'accepting'`)

* `EMBEDDINGS_SYNC` (value: `'embeddings_sync'`)

* `ACCEPTED` (value: `'accepted'`)

* `ACCEPT_FAILED` (value: `'accept_failed'`)

* `REJECTED` (value: `'rejected'`)

* `CANCELLED` (value: `'cancelled'`)

* `UPDATED` (value: `'updated'`)

* `FAILED` (value: `'failed'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


