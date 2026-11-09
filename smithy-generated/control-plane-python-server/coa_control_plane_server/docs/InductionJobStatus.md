# InductionJobStatus

Induction job status.  The first group of stages (PENDING through FAILED) covers the structured induction pipeline (induce_catalog). The second group covers the unstructured induction pipeline stage progression (querying_neptune → sampling → generating_descriptions → resolving_iris → applying_rules → entailment → serializing → storing → completed | failed).

## Enum

* `PENDING` (value: `'pending'`)

* `FETCHING_METADATA` (value: `'fetching_metadata'`)

* `LOADING_GROUNDING_ONTOLOGIES` (value: `'loading_grounding_ontologies'`)

* `GENERATING_EMBEDDINGS` (value: `'generating_embeddings'`)

* `MATCHING` (value: `'matching'`)

* `BUILDING_ONTOLOGY` (value: `'building_ontology'`)

* `STORING` (value: `'storing'`)

* `COMPLETED` (value: `'completed'`)

* `FAILED` (value: `'failed'`)

* `QUERYING_NEPTUNE` (value: `'querying_neptune'`)

* `SAMPLING` (value: `'sampling'`)

* `GENERATING_DESCRIPTIONS` (value: `'generating_descriptions'`)

* `RESOLVING_IRIS` (value: `'resolving_iris'`)

* `APPLYING_RULES` (value: `'applying_rules'`)

* `ENTAILMENT` (value: `'entailment'`)

* `SERIALIZING` (value: `'serializing'`)

* `RUNNING` (value: `'running'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


