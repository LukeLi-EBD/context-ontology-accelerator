# GetEntityResponseContent

One A-Box entity with its class, property, neighbourhood and metric view.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iri** | **str** | Entity IRI. | 
**label** | **str** | Display label. | 
**classes** | [**List[EntityClass]**](EntityClass.md) | Classes asserted or inferred for the entity. | 
**required_properties** | [**List[EntityRequired]**](EntityRequired.md) | Properties required by those classes. | 
**required_status** | **str** | Overall verdict for required properties. | 
**properties** | [**List[EntityProperty]**](EntityProperty.md) | All properties and values on the entity. | 
**neighbors** | [**EntityNeighbors**](EntityNeighbors.md) |  | 
**instance_count** | **float** | Number of instances of the entity&#39;s first class. | 
**related_metrics** | [**EntityRelatedMetrics**](EntityRelatedMetrics.md) |  | 
**sources** | [**List[EntitySource]**](EntitySource.md) | Evidence sources. | 
**evidence_badge** | [**EntityBadge**](EntityBadge.md) |  | 
**tbox** | [**EntityTbox**](EntityTbox.md) |  | [optional] 
**sampled_at** | **str** | When the sample was taken (ISO-8601). | 
**named_graphs** | **List[str]** | Named graphs that supplied the returned statements. | 
**provenance** | [**EntityProvenance**](EntityProvenance.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_entity_response_content import GetEntityResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetEntityResponseContent from a JSON string
get_entity_response_content_instance = GetEntityResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetEntityResponseContent.to_json())

# convert the object into a dict
get_entity_response_content_dict = get_entity_response_content_instance.to_dict()
# create an instance of GetEntityResponseContent from a dict
get_entity_response_content_from_dict = GetEntityResponseContent.from_dict(get_entity_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


