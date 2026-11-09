# ExtractionConfig

Configuration for document extraction behaviour.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**extraction_mode** | [**ExtractionMode**](ExtractionMode.md) |  | [optional] 
**use_batch_inference** | **bool** | Whether to use Bedrock batch inference for extraction. | [optional] 
**enable_versioning** | **bool** | Whether to version extracted documents. | [optional] 
**enable_proposition_extraction** | **bool** | Whether to extract propositions from chunks. | [optional] 
**preferred_entity_classifications** | **List[str]** | Explicit entity-class vocabulary handed to the extraction LLM. When non-empty, overrides both graphrag&#39;s hardcoded news/finance defaults AND the corpus-inferred fallback — the exact labels supplied here are the ones the extractor uses to type entities. Case-sensitive, spaced (e.g. \&quot;Policy\&quot;, \&quot;Claim\&quot;, \&quot;Loss Ratio\&quot;). Leave empty to fall back to inferEntityClassifications. | [optional] 
**infer_entity_classifications** | **bool** | Whether to derive the entity-class vocabulary from this corpus at ingest start rather than inheriting graphrag&#39;s hardcoded news/finance defaults (\&quot;Company\&quot;, \&quot;Sports Team\&quot;, \&quot;Creative Work\&quot;, …). Ignored when preferredEntityClassifications is set. Defaults to true. | [optional] 
**preferred_topics** | **List[str]** | Explicit TOPIC vocabulary handed to the extraction LLM. Topics are the thematic groupings chunks are assigned to — they become &#x60;&#x60;__Topic__&#x60;&#x60; nodes and are later induced as &#x60;&#x60;skos:Concept&#x60;&#x60; — as distinct from preferredEntityClassifications, which types the entities themselves (&#x60;&#x60;__Entity__.class&#x60;&#x60;, induced as &#x60;&#x60;owl:Class&#x60;&#x60;).  The extractor prefers a listed topic when one matches the content in meaning and specificity, and invents a name otherwise, so this is a steer rather than a closed set. Case-sensitive, spaces allowed (e.g. \&quot;Black Tie Gala\&quot;, \&quot;Everyday Elegance\&quot;).  Leave empty (the default) to let the extractor name every topic from the chunk text. There is deliberately no &#x60;&#x60;inferTopics&#x60;&#x60; flag: the toolkit has no topic equivalent of the entity-classification inference pass, so an empty list already *is* \&quot;let the model decide\&quot;. | [optional] 
**enable_table_extraction** | **bool** | Whether to route every PDF through Amazon Textract&#39;s AnalyzeDocument with TABLES feature (instead of unstructured.partition_pdf strategy&#x3D; \&quot;fast\&quot;, which does not detect tables). Preserves row/column structure through preprocessing so a statistical table survives as facts, not prose. Costs materially more per page than DetectDocumentText; leave off for prose-dominant corpora. Defaults to false. | [optional] 
**chunk_size** | **float** | Chunk size (in tokens) for the SentenceSplitter that splits staged documents into extraction/embedding units. Larger values keep more context (a full table row + header, a full policy clause) in one chunk. **&#x60;0&#x60; means \&quot;use the graphrag-toolkit default (256)\&quot;** — the sentinel that survives the state-machine → ECS env-var pipe without a special-cased missing-field state. Set a positive value (e.g. 1024 for dense/tabular corpora) to override. | [optional] 
**chunk_overlap** | **float** | Overlap (in tokens) between consecutive chunks. **&#x60;0&#x60; means \&quot;use the graphrag-toolkit default (25)\&quot;**. Ignored unless chunkSize &gt; 0. | [optional] 
**delete_prev_versions** | **bool** | Whether to delete previous document versions on re-ingest. | [optional] 
**bedrock_model_arn** | **str** | Bedrock inference profile or foundation model ARN. | [optional] 

## Example

```python
from coa_control_plane_server.models.extraction_config import ExtractionConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ExtractionConfig from a JSON string
extraction_config_instance = ExtractionConfig.from_json(json)
# print the JSON string representation of the object
print(ExtractionConfig.to_json())

# convert the object into a dict
extraction_config_dict = extraction_config_instance.to_dict()
# create an instance of ExtractionConfig from a dict
extraction_config_from_dict = ExtractionConfig.from_dict(extraction_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


