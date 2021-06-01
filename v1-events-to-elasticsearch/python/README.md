# Cookbook: "Send Workbench alerts and other detection data to Elasticsearch"

## System Requirements

- Python 3.7 or later
- Elasticsearch 7.2 or later

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
    The following script sends data (Workbench alerts, Observed Attack Technique events, and other detections) from the last five days to Elasticsearch.
    ```text
    (python) $ python v1_events_to_elasticsearch.py -d 5 -D
    ```

## Expected Results

The following sample code writes the number of retrieved Workbench alerts, Observed Attack Technique events, and detections to `stdout`.
```text
Get workbench alerts (0 100): <alert_count>
Get workbench details <alert_detail_count>
Get OAT data(0 200): <oat_count>
Get detection data(<start> <end>): <detection_count>
```

The sample code also indexes the data in Elasticsearch. You can perform the following actions.

- Verify that the Trend Micro Vision One indices exist (Management > Elasticsearch > Index Management).  
    Note: You can replace the prefix "tmv1_" with another lowercase string.
    - tmv1\_workbench
    - tmv1\_observed\_techniques
    - tmv1\_detection
- Check the following data fields:
    - All indices: The time field is "es\_basetime".
    - "workbench" index: A new field called "impactScope.entityString" exists. This is renamed from "impactScope.entityValue".
