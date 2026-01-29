# Datalake Pipeline API Cookbook
This sample demonstrates how to use the Trend Vision One API to manage data pipelines, retrieve data packages, and continuously capture data events.
```mermaid
flowchart TD
    A[Start] --> C{Command Type}
    
    C -->|register| D[Register Data Pipeline]
    C -->|list| E[List Data Pipelines]
    C -->|get| F[Get Pipeline Details]
    C -->|update| G[Update Pipeline]
    C -->|delete| H[Delete Pipeline]
    C -->|list-packages| I[List Pipeline Packages]
    C -->|get-package| J[Get Single Package]
    C -->|continuous-get-packages| K[Start Continuous Capture]
    
    D --> V
    E --> V
    F --> V
    G --> V
    H --> V
    I --> V
    J --> V
    
    K --> Q[Initialize Capture Parameters]
    Q --> R[Wait for Interval]
    R --> S[Fetch Packages]
    S --> T[Save Packages to Bundle]
    T --> U{Continue Capturing?}
    U -->|Yes| R
    U -->|No| V[End]
```

## Related APIs
- [Data Pipeline Management API](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FDatalake-Pipeline)

## Required products
- At least one product connected to Trend Vision One

## Sample code
- [Python](python/)
