# Cookbook: "Modify alert status after checking alert details"

## System Requirements

- Python 3.7 or later

## Environment Setup

1. Install `pipenv`.
    ```text
    $ pip install pipenv
    ```
2. Create a virtual environment for installing packages and managing dependencies.
    ```text
    $ pipenv install
    ```
3. Modify the settings in `check_incident_details.py` to match your environment.
    ```python
    V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
    V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
    ```
    Alternatively, you can set these as environment variables or script command parameters.

## Sample Script

1. Activate the virtual environment associated with your project.
    ```text
    $ pipenv shell
    ```
2. Run a sample script with parameters.  
    The following script retrieves information about all Workbench alerts from the last three days.
    ```text
    (python) $ python check_incident_details.py -d 3
    ```

## Expected Results

The following sample code retrieves Workbench alert details and writes the information to `stdout`.

```text
Get workbench alerts (0 100): <alert_count>

Target Workbench alerts:
[
    // Workbench alert ID list
]

Details for target Workbench alerts:
[
  {
    // Workbench details
  },
  {
    // Workbench details
  },
  ...
]
```
