# QualityCount

A measured count that may be unavailable.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **float** | The measured count, or null when the check could not run. | [optional] 
**detail** | **str** | How the count was measured, or why it is null. | [optional] 

## Example

```python
from coa_control_plane_server.models.quality_count import QualityCount

# TODO update the JSON string below
json = "{}"
# create an instance of QualityCount from a JSON string
quality_count_instance = QualityCount.from_json(json)
# print the JSON string representation of the object
print(QualityCount.to_json())

# convert the object into a dict
quality_count_dict = quality_count_instance.to_dict()
# create an instance of QualityCount from a dict
quality_count_from_dict = QualityCount.from_dict(quality_count_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


