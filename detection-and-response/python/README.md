# Cookbook: "Take a response action on the highlighted object in a Workbench alert"

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
3. Modify the settings in `detection_and_response.py` to match your environment.
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
    The following script executes detection and response commands for Workbench alerts that were received in the last three days.
    ```text
    (python) $ python detection_and_response.py -d 3
    ```

## Expected Results

The following sample code writes information about new Workbench alerts and response actions taken on affected entities to `stdout`.

```text
Get workbench alerts (0 100): <alert_count>

Target workbench alerts:
[
    // New workbench alert ID list
]

Handle impacted entities: <entity_count>

Isolated endpoints IP address:
[
    // Isolated IP address list
]

Quarantined message subject:
[
    // Quarantined message subject list
]
```
