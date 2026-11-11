# EntityMention

One entity mention in the question: a matched ontology entity or an unresolved content fragment counted as one missing entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** | Surface text as it appears in the normalized question (known entities use the matched label). | 
**span** | **List[float]** | Inclusive-exclusive [start, end) character span in the normalized question. | 
**kind** | **str** | &#x60;ontology&#x60; when the mention matched a term, &#x60;unknown&#x60; otherwise. | 
**term** | **str** | Matched term IRI (ontology mentions only). | [optional] 
**label** | **str** | Matched label (ontology mentions only). | [optional] 
**source** | **str** | Label source of the match: &#x60;skos&#x60; or &#x60;rdfs:label&#x60;. | [optional] 

## Example

```python
from coa_data_layer_server.models.entity_mention import EntityMention

# TODO update the JSON string below
json = "{}"
# create an instance of EntityMention from a JSON string
entity_mention_instance = EntityMention.from_json(json)
# print the JSON string representation of the object
print(EntityMention.to_json())

# convert the object into a dict
entity_mention_dict = entity_mention_instance.to_dict()
# create an instance of EntityMention from a dict
entity_mention_from_dict = EntityMention.from_dict(entity_mention_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


