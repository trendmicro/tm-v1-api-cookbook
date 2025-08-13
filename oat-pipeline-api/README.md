# Observed Attack Techniques Data Pipeline
This sample demonstrates how to use the Trend Vision One API to manage Observed Attack Techniques data pipelines, retrieve packages of Observed Attack Techniques data, and continuously capture Observed Attack Techniques events.
```mermaid
flowchart TD
    A[Start] --> C{Command Type}
    
    C -->|register| D[Register Data Pipeline]
    C -->|list| E[List Data Pipelines]
    C -->|get| F[Get Pipeline Details]
    C -->|delete| G[Delete Pipeline]
    C -->|list-packages| H[List Pipeline Packages]
    C -->|get-package| I[Get Single Package]
    C -->|continuous-get-packages| J[Start Continuous Capture]
    
    D --> V
    E --> V
    F --> V
    G --> V
    H --> V
    I --> V
    
    J --> Q[Initialize Capture Parameters]
    Q --> R[Wait for Interval]
    R --> S[Fetch Packages]
    S --> T[Save Packages to Bundle]
    T --> U{Continue Capturing?}
    U -->|Yes| R
    U -->|No| V[End]
```

## Related APIs
- [Get Observed Attack Techniques events](https://automation.trendmicro.com/xdr/api-v3#tag/Observed-Attack-Techniques/paths/~1v3.0~1oat~1detections/get)

## Required products
- At least one product connected to Trend Vision One

## Sample code
- [Python](python/)
