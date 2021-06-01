# Cookbook: "Perform threat hunting based on IoCs from a source"

## System Requirements

- Python 3.7 or later
- TAXII 2.0 or 2.1 server

## Environment Setup

1. Install `pipenv`.
    ```text
    $ pip install pipenv
    ```
2. Create a virtual environment for installing packages and managing dependencies.
    ```text
    $ pipenv install
    ```
3. Modify the settings in `taxii_ioc_hunting.py` to match your environment.
    ```python
    V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
    V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
    TAXII_URL = os.environ.get('TMV1_TAXII_URL', '')
    TAXII_USER = os.environ.get('TMV1_TAXII_USER')
    TAXII_PASSWORD = os.environ.get('TMV1_TAXII_PASSWORD')
    ```
    Alternatively, you can set these as environment variables or script command parameters.

## Sample Script

1. Activate the virtual environment associated with your project.
    ```text
    $ pipenv shell
    ```
2. Run a sample script with parameters.  
    The following script searches for IoCs in endpoint activity data from the last three days.
    ```text
    (python) $ python taxii_ioc_hunting.py -d 3
    ```

## Expected Results

The following sample code retrieves STIX objects from the TAXII server, extracts IoCs from the STIX objects, searches the IoCs in endpoint activity data, and writes the search results to `stdout`.

```text
Get STIX objects from TAXII server: <objects_count>

Searchable IoCs from TAXII server:
{
  "domain": [
      // Domain related IoCs
  ],
  "url": [
      // URL related IoCs
  ],
  "ipaddr": [
      // IP address related IoCs
  ],
  "sha1": [
      // File SHA1 related IoCs
  ]
}

IoC hits in endpoint activities:
{
  "data": {
    "logs": [
      {
          // Search API result1
      },
      {
          // Search API result2
      },
      ...
    ],
    "total_count": <total_search_results>,
    "offset": 0
  }
}
```
