# CoverageChars

Character accounting behind the ontology/term coverage ratio.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**covered** | **float** | Number of content characters covered by a matched term. | 
**total** | **float** | Number of content characters in the question (stopwords/punctuation removed). | 

## Example

```python
from coa_data_layer_server.models.coverage_chars import CoverageChars

# TODO update the JSON string below
json = "{}"
# create an instance of CoverageChars from a JSON string
coverage_chars_instance = CoverageChars.from_json(json)
# print the JSON string representation of the object
print(CoverageChars.to_json())

# convert the object into a dict
coverage_chars_dict = coverage_chars_instance.to_dict()
# create an instance of CoverageChars from a dict
coverage_chars_from_dict = CoverageChars.from_dict(coverage_chars_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


