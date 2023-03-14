# Take a response action on the highlighted object in a Workbench alert
This task identifies the highlighted object in a Workbench alert and then takes a response action on that object.
```mermaid
graph LR;
s(Start)-->action_list_alerts[Retrieve<br>new Workbench alerts];
action_list_alerts-->check_new_alerts{Are new alerts<br>available?};
check_new_alerts--Yes-->action_update_status[Update<br>alert status];
action_update_status-->check_indicator_type{Indicators'<br>type};
check_indicator_type--Supported<br>type-->action_register_iocs[Register IoCs as<br>suspicious objects];
action_register_iocs-->check_impact_scope{Impact<br>scope};
check_indicator_type--Others-->check_impact_scope;
check_impact_scope--Email-->action_search_email[Search<br>email message details];
action_search_email-->action_quarantine_email[Create quarantine<br>email message task];
check_impact_scope--Endpoint-->check_supported_products{Supported<br>product};
check_supported_products--Yes-->action_query_endpoint[Query<br>endpoint information];
action_query_endpoint-->action_isolate_endpoint[Create isolate<br>endpoint task];
action_quarantine_email-->action_wait_complete[Wait for<br>response];
action_isolate_endpoint-->action_wait_complete;
action_wait_complete-->action_add_note[Add<br>alert notes];
check_impact_scope--Others-->action_add_note;
check_supported_products--No-->action_add_note;
action_add_note-->e(End);
check_new_alerts--No-->e;
```

## Related APIs
- [Get alerts list](https://automation.trendmicro.com/xdr/api-v3#tag/Workbench/paths/~1v3.0~1workbench~1alerts/get)
- [Modify alert status](https://automation.trendmicro.com/xdr/api-v3#tag/Workbench/paths/~1v3.0~1workbench~1alerts~1{id}/patch)
- [Get endpoint data](https://automation.trendmicro.com/xdr/api-v3#tag/Search/paths/~1v3.0~1eiqs~1endpoints/get)
- [Isolate endpoints](https://automation.trendmicro.com/xdr/api-v3#tag/Endpoint/paths/~1v3.0~1response~1endpoints~1isolate/post)
- [Get email activity data](https://automation.trendmicro.com/xdr/api-v3#tag/Search/paths/~1v3.0~1search~1emailActivities/get)
- [Quarantine email message](https://automation.trendmicro.com/xdr/api-v3#tag/Email/paths/~1v3.0~1response~1emails~1quarantine/post)

## Required products
- At least one of the following: Deep Security, Trend Cloud One - Workload Security, Trend Micro Apex One, Trend Micro Apex One (Mac), XDR Endpoint Sensor
- Cloud App Security

## Sample code
- [Python](python/)
