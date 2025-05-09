# Cookbook: "Send Workbench alerts, audit logs, and other detection data to Elasticsearch"

## System Requirements

- Python 3.9 or later
- Elasticsearch 8.4.1 or later

## Environment Setup

1. Install `pipenv`.
    ```text
    $ pip install pipenv
    ```
2. Create a virtual environment for installing packages and managing dependencies.
    ```text
    $ pipenv install
    ```
3. Modify the settings in `v1_events_to_elasticsearch.py` to match your environment.
    ```python
    V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
    V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
    V1_UA = os.environ.get('TMV1_UA', f'Trend Vision One API Cookbook ({os.path.basename(__file__)})')
    ES_URL = os.environ.get('TMV1_ELASTICSEARCH_URL', 'http://localhost:9200')
    ES_INDEX_PREFIX = os.environ.get('TMV1_ELASTICSEARCH_INDEX_PREFIX', 'tmv1_')
    ES_USER = os.environ.get('TMV1_ELASTICSEARCH_USER')
    ES_PASSWORD = os.environ.get('TMV1_ELASTICSEARCH_PASSWORD')
    ES_CAFILE = os.environ.get('TMV1_ELASTICSEARCH_CAFILE')
    ES_CAPATH = os.environ.get('TMV1_ELASTICSEARCH_CAPATH')
    ES_CERTFILE = os.environ.get('TMV1_ELASTICSEARCH_CERTFILE')
    ES_KEYFILE = os.environ.get('TMV1_ELASTICSEARCH_KEYFILE')
    ```
    Alternatively, you can set these as environment variables or script command parameters.

## Sample Script

1. Activate the virtual environment associated with your project.
    ```text
    $ pipenv shell
    ```
2. Run a sample script with parameters.  
    The following script sends data (Workbench alerts, Observed Attack Technique events, audit logs, and other detections) from the last five days to Elasticsearch.
    ```text
    (python) $ python v1_events_to_elasticsearch.py -d 5 -D -a
    ```

## Expected Results

The following sample code writes the number of retrieved Workbench alerts, Observed Attack Technique events, audit logs, and detections to `stdout`.

```text
Retrieved workbench alerts: <alert_count>
Retrieved Observed Attack Techniques events: <oat_count>
Retrieved detections: <detection_count>
Retrieved audit logs: <audit_log_count>
```

The sample code also indexes the data in Elasticsearch. You can perform the following actions.

- Verify that the Trend Vision One indices exist (Management > Elasticsearch > Index Management).  
    - tmv1\_workbench
    - tmv1\_observed\_techniques
    - tmv1\_detection
    - tmv1\_audit\_logs

    You can replace the prefix `tmv1_` with another lowercase string.

- Check the following data fields:
    - All indices: The time field is "esBaseDateTime".
    - "workbench" index: A new field called "impactScope.\<type name\>" exists. This is renamed from "impactScope.entityValue" to the "\<type name\>" specified by the "entityType" field.
    - "workbench" index: A new field called "indicators.\<type name\>" exists. This is renamed from "indicators.value" to the "\<type name\>" specified by the "type" field combined with the the type name of the value.
    - "workbench" index: A new field called "severity" exists. This is renamed to "severityString".
    - "observed techniques" index: A new field called "filters.highlightedObjects.\<type name\>" exists. This is renamed from "filters.highlightedObjects.value" to the "\<type name\>" specified by the "type" field.
 
      The value of a "text" field is converted to string when necessary.

   - "observed techniques" index: A new field called "detail" exists. This is renamed to the "\<source name\>" specified by the "source" field.
