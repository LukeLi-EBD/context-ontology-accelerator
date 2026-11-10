# ListFactsResponseContent

Facts matching a `ListFacts` query.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | **str** | State filter that produced this page; &#x60;all&#x60; when not narrowed. | 
**items** | [**List[FactRecord]**](FactRecord.md) | Rows in ledger order. | 
**count** | **float** | Number of rows in this page. | 
**conflicts** | [**List[FactConflict]**](FactConflict.md) | Conflict groups touching the returned rows. | [optional] 

## Example

```python
from coa_control_plane_server.models.list_facts_response_content import ListFactsResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of ListFactsResponseContent from a JSON string
list_facts_response_content_instance = ListFactsResponseContent.from_json(json)
# print the JSON string representation of the object
print(ListFactsResponseContent.to_json())

# convert the object into a dict
list_facts_response_content_dict = list_facts_response_content_instance.to_dict()
# create an instance of ListFactsResponseContent from a dict
list_facts_response_content_from_dict = ListFactsResponseContent.from_dict(list_facts_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


