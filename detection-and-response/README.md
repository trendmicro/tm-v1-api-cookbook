# Take a response action on the highlighted object in a Workbench alert
This task identifies the highlighted object in a Workbench alert and then takes a response action on that object.
```mermaid
graph LR;
s(Start)-->a1[Retrieve<br>new Workbench alerts];
a1-->cc1{Are new alerts<br>available?};
cc1--Yes-->a2[Update<br>alert status];
a2-->cc2{Impact<br>scope};
cc2--Email-->a3[Search<br>email message details];
a3-->a4[Quarantine<br>email message];
cc2--Endpoint-->cc3{Supported<br>products};
cc3--Yes-->a5[Isolate<br>endpoint];
a4-->a6[Add<br>alert notes];
a5-->a6;
cc2--Others-->a6;
cc3--Others-->a6;
a6-->e(End);
cc1--No-->e;
```

## Related APIs
- [Get alert history with details](https://automation.trendmicro.com/xdr/api-v2#tag/Alerts/paths/~1v2.0~1xdr~1workbench~1workbenchHistories/get)
- [Edit alert status](https://automation.trendmicro.com/xdr/api-v2#tag/Alerts/paths/~1v2.0~1xdr~1workbench~1workbenches~1{workbenchId}/put)
- [Query information for multiple endpoints](https://automation.trendmicro.com/xdr/api-v2#tag/Search/paths/~1v2.0~1xdr~1eiqs~1query~1batch~1endpointInfo/post)
- [Isolate endpoint](https://automation.trendmicro.com/xdr/api-v2#tag/Endpoint/paths/~1v2.0~1xdr~1response~1isolate/post)
- [Search for data and list all results](https://automation.trendmicro.com/xdr/api-v2#tag/Search/paths/~1v2.0~1xdr~1search~1data/post)
- [Quarantine email message](https://automation.trendmicro.com/xdr/api-v2#tag/Email/paths/~1v2.0~1xdr~1response~1quarantineMessage/post)
- [Add alert note](https://automation.trendmicro.com/xdr/api-v2#tag/Notes/paths/~1v2.0~1xdr~1workbench~1workbenches~1{workbenchId}~1notes/post)

## Required products
- At least one of the following: Deep Security, Trend Cloud One - Workload Security, Trend Micro Apex One, Trend Micro Apex One (Mac), XDR Endpoint Sensor
- Cloud App Security

## Sample code
- [Python](python/)
