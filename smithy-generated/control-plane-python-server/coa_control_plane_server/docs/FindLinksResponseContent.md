# FindLinksResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**nodes** | [**List[GraphLinkNode]**](GraphLinkNode.md) | Neighbours within the hop limit, nearest first; the seed is omitted. | 
**edges** | [**List[GraphLinkEdge]**](GraphLinkEdge.md) | Adjacency edges within the hop limit, deduplicated by triple + graph. | 
**truncated** | **bool** | True when the edge limit ended the expansion before it was complete. | 

## Example

```python
from coa_control_plane_server.models.find_links_response_content import FindLinksResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of FindLinksResponseContent from a JSON string
find_links_response_content_instance = FindLinksResponseContent.from_json(json)
# print the JSON string representation of the object
print(FindLinksResponseContent.to_json())

# convert the object into a dict
find_links_response_content_dict = find_links_response_content_instance.to_dict()
# create an instance of FindLinksResponseContent from a dict
find_links_response_content_from_dict = FindLinksResponseContent.from_dict(find_links_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


