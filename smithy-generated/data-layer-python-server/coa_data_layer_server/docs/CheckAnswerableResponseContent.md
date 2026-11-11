# CheckAnswerableResponseContent

Result of an answerability pre-check.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** | Echo of the checked question. | 
**answerable** | **bool** | True when the question can be answered: term coverage meets the threshold, or an exact metric match supports a definition answer even when no fact rows are available. | 
**value_answerable** | **bool** | True when a concrete numeric value can be produced (facts layer covered). | 
**answer_mode** | **str** | How the question can be answered: &#x60;value&#x60;, &#x60;definition&#x60; or &#x60;none&#x60;. | 
**intent** | **str** | Detected question intent: &#x60;value&#x60; or &#x60;definition&#x60;. | 
**degraded** | **bool** | True when any layer is degraded or unavailable. | 
**coverage** | **float** | Character coverage of the ontology/term layer (0..1). | 
**threshold** | **float** | Threshold used to decide &#x60;answerable&#x60;. | 
**coverage_chars** | [**CoverageChars**](CoverageChars.md) |  | 
**ontology_version** | **str** | Ontology version the check ran against. | 
**ontology_graph** | **str** | Named graph URI of that version. | 
**term_source** | **str** | Human-readable description of the term source used. | 
**term_count** | **float** | Number of distinct terms considered. | 
**matched_terms** | [**List[MatchedTerm]**](MatchedTerm.md) | Terms that matched the question. | 
**layers** | [**List[CoverageLayer]**](CoverageLayer.md) | Exactly four layers, in order: ontology, terms, metrics, facts. | 
**missing** | [**List[MissingGap]**](MissingGap.md) | One entry per gap, each carrying what is missing and how to fix it (F79). | 
**candidates** | [**List[AnswerCandidate]**](AnswerCandidate.md) | Ranked candidates that could close the gaps. | 
**reasons** | **List[str]** | Machine-readable reasons collected while evaluating. | 
**reason_code** | **str** | Machine-readable reason when &#x60;answerable&#x60; is false. | [optional] 
**hint** | **str** | Operator-facing next step when &#x60;answerable&#x60; is false. | [optional] 
**timings** | [**AnswerTimings**](AnswerTimings.md) |  | 

## Example

```python
from coa_data_layer_server.models.check_answerable_response_content import CheckAnswerableResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of CheckAnswerableResponseContent from a JSON string
check_answerable_response_content_instance = CheckAnswerableResponseContent.from_json(json)
# print the JSON string representation of the object
print(CheckAnswerableResponseContent.to_json())

# convert the object into a dict
check_answerable_response_content_dict = check_answerable_response_content_instance.to_dict()
# create an instance of CheckAnswerableResponseContent from a dict
check_answerable_response_content_from_dict = CheckAnswerableResponseContent.from_dict(check_answerable_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


