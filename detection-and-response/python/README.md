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
    V1_UA = os.environ.get('TMV1_UA', f'Trend Micro Vision One API Cookbook ({os.path.basename(__file__)})')
    V1_WAIT_TASK_INTERVAL = int(os.environ.get('TMV1_WAIT_TASK_INTERVAL', 10))
    V1_WAIT_TASK_RETRY = int(os.environ.get('TMV1_WAIT_TASK_RETRY', 12))
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
Retrieved workbench alerts: <alert_count>
Added suspicious objects: <added_suspicious_object_count>
Tasks running: <running_tasks_count>; Waiting interval (seconds): <interval_seconds>; Number of intervals: <retry_count>.
Isolated endpoints: <isolated_endpoint_count>
Tasks running: <running_tasks_count>; Waiting interval (seconds): <interval_seconds>; Number of intervals: <retry_count>.
Quarantined emails: <quarantined_email_count>
Tasks running: <running_tasks_count>; Waiting interval (seconds): <interval_seconds>; Number of intervals: <retry_count>.

Alert ID: <alert_id>
Object <suspicious_o-bject_type> "<suspicious_object_value>" added to Suspicious Object List successfully.
Endpoint "<endpoint_name>" isolated successfully.
Message for "<mail_address>" quarantined successfully.
```
