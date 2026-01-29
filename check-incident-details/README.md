# Modify alert status after checking alert details
This task retrieves data about incident-related Workbench alerts and then modifies the status of these alerts after investigation is completed.
```mermaid
graph LR;
s[Start] --> a1[Retrieve<br>Workbench alerts];
a1 --> a2[Parse<br>alert details];
a2 --> a3[Update<br>alert status];
a3 --> a4[List<br>alert details];
a4 --> e[End];
```

## Related APIs
- [Get alerts list](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FWorkbench%2Fpaths%2F~1v3.0~1workbench~1alerts%2Fget)
- [Modify alert status](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FWorkbench%2Fpaths%2F~1v3.0~1workbench~1alerts~1%7Bid%7D%2Fpatch)

## Required products
- At least one Trend Micro product that connects to Trend Vision One

## Sample code
- [Python](python/)
