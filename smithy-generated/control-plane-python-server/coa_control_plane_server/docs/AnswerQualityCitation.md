# AnswerQualityCitation

One citation attached to an answer.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Citation identifier. | 
**kind** | **str** | Citation kind, e.g. &#x60;document&#x60; or &#x60;fact&#x60;. | 
**ref** | **str** | Referenced identifier. | 
**version_id** | **str** | Ontology or document version the citation resolved against. | [optional] 
**resolve_url** | **str** | Console URL that resolves the citation. | [optional] 
**resolvable** | **bool** | True when the reference still resolves. | 

## Example

```python
from coa_control_plane_server.models.answer_quality_citation import AnswerQualityCitation

# TODO update the JSON string below
json = "{}"
# create an instance of AnswerQualityCitation from a JSON string
answer_quality_citation_instance = AnswerQualityCitation.from_json(json)
# print the JSON string representation of the object
print(AnswerQualityCitation.to_json())

# convert the object into a dict
answer_quality_citation_dict = answer_quality_citation_instance.to_dict()
# create an instance of AnswerQualityCitation from a dict
answer_quality_citation_from_dict = AnswerQualityCitation.from_dict(answer_quality_citation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


