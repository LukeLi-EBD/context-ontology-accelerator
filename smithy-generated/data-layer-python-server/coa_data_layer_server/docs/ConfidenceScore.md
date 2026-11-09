# ConfidenceScore

A confidence score in [0, 1] for a query result, with an optional rationale explaining how it was derived.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**score** | **float** | Confidence score in the range [0, 1]. | 
**rationale** | **str** | Explanation of how the score was derived. | [optional] 

## Example

```python
from coa_data_layer_server.models.confidence_score import ConfidenceScore

# TODO update the JSON string below
json = "{}"
# create an instance of ConfidenceScore from a JSON string
confidence_score_instance = ConfidenceScore.from_json(json)
# print the JSON string representation of the object
print(ConfidenceScore.to_json())

# convert the object into a dict
confidence_score_dict = confidence_score_instance.to_dict()
# create an instance of ConfidenceScore from a dict
confidence_score_from_dict = ConfidenceScore.from_dict(confidence_score_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


