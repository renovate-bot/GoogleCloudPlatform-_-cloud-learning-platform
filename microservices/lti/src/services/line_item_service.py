"""Line item service"""
from common.models import LineItem, LTIContentItem


def create_new_line_item(input_line_item_dict):
  """Creates a new line item"""
  new_line_item = LineItem()
  new_line_item = new_line_item.from_dict(input_line_item_dict)
  new_line_item.save()
  return new_line_item


def create_new_content_item(input_content_item_dict, context_id=None):
  """Creates a new content item"""
  new_content_item = LTIContentItem()
  new_content_item = new_content_item.from_dict(input_content_item_dict)
  new_content_item.save()
  content_item_fields = new_content_item.get_fields(reformat_datetime=True)

  content_item_info = input_content_item_dict.get("content_item_info")

  if "lineItem" in content_item_info.keys():
    line_item_data = content_item_info.get("lineItem")

    start_date_time = ""
    end_date_time = ""

    if content_item_info.get("available", ""):
      start_date_time = content_item_info.get("available",
                                              "").get("startDateTime", "")
      end_date_time = content_item_info.get("available",
                                            "").get("endDateTime", "")

    input_line_item = {
        "startDateTime": start_date_time,
        "endDateTime": end_date_time,
        "scoreMaximum": line_item_data.get("scoreMaximum"),
        "label": line_item_data.get("label"),
        "tag": line_item_data.get("tag", ""),
        "resourceId": line_item_data.get("resourceId", ""),
        "resourceLinkId": new_content_item.id,
        "contextId": context_id
    }
    create_new_line_item(input_line_item)

  content_item_fields["id"] = new_content_item.id
  return content_item_fields
