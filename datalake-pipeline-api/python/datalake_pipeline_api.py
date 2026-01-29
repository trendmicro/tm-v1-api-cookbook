import argparse
import datetime
import json
import os
import pathlib
import signal
import sys
import time
import uuid

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util import Retry


# Environment variables for configuration
V1_TOKEN = os.environ.get("TMV1_TOKEN", "")
# Specify the correct domain name for your region in V1_URL
#   default: https://api.xdr.trendmicro.com (US region)
V1_URL = os.environ.get("TMV1_URL", "https://api.xdr.trendmicro.com")
# This value is used for User-Agent header in API requests
V1_UA = os.environ.get(
    "TMV1_UA",
    f"Trend Vision One API Cookbook ({os.path.basename(__file__)})"
)


class TmV1Client:
    base_url_default = V1_URL
    # Telemetry subtypes from API documentation
    telemetry_subtypes = [
        "endpointActivity",
        "cloudActivity",
        "emailActivity",
        "mobileActivity",
        "networkActivity",
        "containerActivity",
        "identityActivity",
        "all"
    ]
    # Top parameter choices for paginated endpoints
    packages_top_choices = [50, 100, 200, 500, 1000, 5000]
    # Interval choices for continuous operations (in seconds)
    interval_choices = [60, 120, 180, 300, 600]

    def __init__(self, token, base_url=None):
        if not token:
            raise ValueError("Authentication token missing")
        self.endpoint_url = (base_url or self.base_url_default) + "{api}"
        self.jwt = token
        self.session = Session()
        self.user_agent = V1_UA
        retry = Retry(
            total=5,
            status_forcelist=[429, 502, 504],
            allowed_methods=["GET"],
            backoff_factor=1,
        )
        http_adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", http_adapter)

    def get_headers(self):
        return {
            'x-trace-id': str(uuid.uuid4()),
            "x-task-id": str(uuid.uuid4()),
            "Authorization": f"Bearer {self.jwt}",
            "User-Agent": self.user_agent,
        }

    def get_items(self, api_path, **kwargs):
        """
        Generic method to get all items from a paginated API endpoint.
        Args:
            api_path (str): The API path to request
            **kwargs: Additional parameters to pass to the request
        Returns:
            dict: Response with all items combined from all pages
        """
        items = []
        next_link = None
        last_response = None
        while True:
            try:
                if next_link is None:
                    resp = self.session.get(
                        self.endpoint_url.format(api=api_path),
                        headers=self.get_headers(),
                        **kwargs
                    )
                else:
                    resp = (
                        self.session.get(next_link, headers=self.get_headers())
                    )
                print(
                    f'resp={resp}, '
                    f'trace-id={resp.headers.get("x-trace-id")}'
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Request unsuccessful (GET {api_path}): "
                        f"{resp.status_code} {resp.text}"
                    )
            except RequestException as e:
                error_message = (
                    f'Request unsuccessful (GET {api_path}): '
                    f'{getattr(e.response, "status_code", "N/A")} '
                    f'{getattr(e.response, "text", str(e))}'
                )
                raise RuntimeError(error_message) from e
            result = resp.json()
            last_response = result
            # Add items from this page
            if "items" in result:
                items.extend(result["items"])
            # Check for next page
            next_link = result.get("nextLink")
            if not next_link:
                break
        # Create a response that mimics the API structure but with all items
        return {
            "items": items,
            # Include other metadata from the last response if needed
            **{k: v for k, v in last_response.items()
               if k != "items" and k != "nextLink"}
        }

    def get_datapipelines(self):
        """
        Displays all data pipelines that have a data type assigned.
        Returns:
            dict: The response JSON containing all data pipelines
        """
        api = "/v3.0/datalake/dataPipelines"
        try:
            resp = self.session.get(
                self.endpoint_url.format(api=api),
                headers=self.get_headers()
            )
            print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
            if resp.status_code != 200:
                raise RuntimeError(
                    f'Request unsuccessful (GET {api}): '
                    f'{resp.status_code} {resp.text}'
                )
        except RequestException as e:
            error_message = (
                f'Request unsuccessful (GET {api}): '
                f'{getattr(e.response, "status_code", "N/A")} '
                f'{getattr(e.response, "text", str(e))}'
            )
            raise RuntimeError(error_message) from e
        return resp.json()

    def register_datapipeline(self, data_type, description, sub_type=None):
        """
        Bind a data type to a pipeline
        Args:
            data_type (str): Type of data for the pipeline
            description (str): Description of the pipeline
            sub_type (list, optional): List of subtypes for the pipeline
        Returns:
            str: The location header containing the created pipeline ID
        """
        api = "/v3.0/datalake/dataPipelines"
        payload = {"type": data_type, "description": description}
        if sub_type:
            payload["subType"] = sub_type
        try:
            resp = self.session.post(
                self.endpoint_url.format(api=api),
                headers=self.get_headers(), json=payload
            )
            print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
            if resp.status_code not in [200, 201]:
                raise RuntimeError(
                    f'Request unsuccessful (POST {api}): '
                    f'{resp.status_code} {resp.text}'
                )
        except RequestException as e:
            error_message = (
                f'Request unsuccessful (POST {api}): '
                f'{getattr(e.response, "status_code", "N/A")} '
                f'{getattr(e.response, "text", str(e))}'
            )
            raise RuntimeError(error_message) from e
        return resp.headers.get("Location")

    def get_datapipeline(self, pipeline_id):
        """
        Displays information about the specified data pipeline.
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
        Returns:
            dict: The response JSON containing pipeline details
        """
        api = f"/v3.0/datalake/dataPipelines/{pipeline_id}"
        try:
            resp = self.session.get(
                self.endpoint_url.format(api=api),
                headers=self.get_headers()
            )
            print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
            if resp.status_code != 200:
                raise RuntimeError(
                    f'Request unsuccessful (GET {api}): '
                    f'{resp.status_code} {resp.text}'
                )
        except RequestException as e:
            error_message = (
                f'Request unsuccessful (GET {api}): '
                f'{getattr(e.response, "status_code", "N/A")} '
                f'{getattr(e.response, "text", str(e))}'
            )
            raise RuntimeError(error_message) from e
        return resp.json()

    def update_datapipeline(
        self, pipeline_id, data_type=None, sub_type=None, description=None
    ):
        """
        Updates the settings of the specified data pipeline.
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
            data_type (str, optional): Type of data for the pipeline
            sub_type (list, optional): List of subtypes for the pipeline
            description (str, optional): Description of the pipeline
        Returns:
            dict: The response JSON from the API
        """
        api = f"/v3.0/datalake/dataPipelines/{pipeline_id}"
        request_body = {}
        if data_type is not None:
            request_body["type"] = data_type
        if sub_type is not None:
            request_body["subType"] = sub_type
        if description is not None:
            request_body["description"] = description
        try:
            resp = self.session.patch(
                self.endpoint_url.format(api=api),
                headers=self.get_headers(),
                json=request_body,
            )
            print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
            if resp.status_code != 204:
                raise RuntimeError(
                    f'Request unsuccessful (PATCH {api}): '
                    f'{resp.status_code} {resp.text}'
                )
            print(
                f"Status Code: {resp.status_code}, "
                f"Response Text: {resp.text}, "
                f'trace-id={resp.headers.get("x-trace-id")}'
            )
        except RequestException as e:
            error_message = (
                f'Request unsuccessful (PATCH {api}): '
                f'{getattr(e.response, "status_code", "N/A")} '
                f'{getattr(e.response, "text", str(e))}'
            )
            raise RuntimeError(error_message) from e

    def get_datapipeline_packages(
        self, pipeline_id,
        start_datetime, end_datetime,
        top=500
    ):
        """
        Display all the available packages
        from a data pipeline a paginated list.
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
            start_datetime (str): Start date/time for package search
            end_datetime (str): End date/time for package search
            top (int, optional): Maximum number of results to return
        Returns:
            dict: The response JSON containing package information
        """
        api = f"/v3.0/datalake/dataPipelines/{pipeline_id}/packages"
        params = {
            "startDateTime": start_datetime,
            "endDateTime": end_datetime,
            "top": top,
        }
        return self.get_items(api, params=params)

    def get_datapipeline_package(self, pipeline_id, package_id):
        """
        Retrieve the specified data pipeline package.
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
            package_id (str): Unique identifier for the package
        Returns:
            bytes: The raw package data
        """
        api = (
            f"/v3.0/datalake/dataPipelines/{pipeline_id}"
            f"/packages/{package_id}"
        )
        resp = self.session.get(
            self.endpoint_url.format(api=api),
            headers=self.get_headers(), stream=True
        )
        print(
            f"resp={resp}, "
            f'trace-id={resp.headers.get("x-trace-id")}'
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f'Request unsuccessful (GET {api}): '
                f'{resp.status_code} {resp.text}'
            )
        return resp.raw.read()

    def delete_datapipeline(self, pipeline_id_list):
        """
        Unbind data type from pipeline(s)
        Args:
            pipeline_id_list (list): List of pipeline IDs to delete
        Returns:
            list: A list containing a single dictionary
            with status code and message
        """
        api = "/v3.0/datalake/dataPipelines/delete"
        try:
            resp = self.session.post(
                self.endpoint_url.format(api=api),
                headers=self.get_headers(),
                json=[{"id": p} for p in pipeline_id_list],
            )
            print(
                f"resp={resp}, "
                f'trace-id={resp.headers.get("x-trace-id")}'
            )
            if resp.status_code != 207:
                raise RuntimeError(
                    f'Request unsuccessful (POST {api}): '
                    f'{resp.status_code} {resp.text}'
                )
        except RequestException as e:
            error_message = (
                f'Request unsuccessful (POST {api}): '
                f'{getattr(e.response, "status_code", "N/A")} '
                f'{getattr(e.response, "text", str(e))}'
            )
            raise RuntimeError(error_message) from e
        return [{
            "status": resp.status_code,
            "message": "Pipeline(s) successfully deleted"
        }]


def signal_int_handler(sig, frame):
    """
    Handler for SIGINT signal to stop continuous package retrieval.
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    print("stop capturing")
    global CAPTURING
    CAPTURING = False


# flag to indicate if continue in continuous-get-packages mode
CAPTURING = True


def main(args):
    """
    Main function that handles command line arguments
    and executes API operations.
    Args:
        args: Parsed command line arguments
    """
    url = args.v1_url
    token = args.v1_token
    if args.token_file and not token:
        try:
            with open(args.token_file) as fd:
                token = fd.read().strip()
        except FileNotFoundError:
            print(f"Token not found: {args.token_file}")
            sys.exit(1)
    client = TmV1Client(token, url)
    if args.request == "register":
        print(
            f"request: {args.request}, "
            f"args: type={args.type}, "
            f"description={args.description}"
        )
        result = client.register_datapipeline(
            data_type=args.type,
            description=args.description,
            sub_type=args.sub_type
        )
        print(result)
    elif args.request == "list":
        print(f"request: {args.request}")
        result = client.get_datapipelines()
        print(json.dumps(result, indent=2))
    elif args.request == "get":
        print(
            f"request: {args.request},"
            f"args: pipeline_id={args.pipeline_id}"
        )
        result = client.get_datapipeline(pipeline_id=args.pipeline_id)
        print(json.dumps(result, indent=2))
    elif args.request == "update":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id={args.pipeline_id}, "
            f"type={args.type}, sub_type={args.sub_type}, "
            f"description={args.description}"
        )
        client.update_datapipeline(
            pipeline_id=args.pipeline_id,
            data_type=args.type,
            sub_type=args.sub_type,
            description=args.description,
        )
        print("Pipeline updated successfully")
    elif args.request == "delete":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id_list={args.pipeline_id}"
        )
        result = client.delete_datapipeline(pipeline_id_list=args.pipeline_id)
        print(json.dumps(result, indent=2))
    elif args.request == "list-packages":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id={args.pipeline_id}, "
            f"start_datetime={args.start_datetime}, "
            f"end_datetime={args.end_datetime}, "
            f"top={args.top}, "
        )
        result = client.get_datapipeline_packages(
            pipeline_id=args.pipeline_id,
            start_datetime=args.start_datetime,
            end_datetime=args.end_datetime,
            top=args.top
        )
        print(json.dumps(result, indent=2))
    elif args.request == "get-package":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id={args.pipeline_id}, "
            f"package_id={args.package_id}, output={args.output}"
        )
        output_path = pathlib.Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = client.get_datapipeline_package(
            pipeline_id=args.pipeline_id, package_id=args.package_id
        )
        with open(output_path, "wb") as fd:
            fd.write(result)
    elif args.request == "continuous-get-packages":
        output_path = pathlib.Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        signal.signal(signal.SIGINT, signal_int_handler)
        interval = args.interval
        pipeline_id = args.pipeline_id
        start_datetime = datetime.datetime.now(tz=datetime.timezone.utc)
        end_datetime = start_datetime + datetime.timedelta(seconds=interval)
        process_start = time.time()
        print(
            "start capturing..., next request is around: ",
            end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        while CAPTURING:
            if time.time() - process_start > interval:
                # Get all packages for the current time interval using
                # get_items (via get_datapipeline_packages)
                packages_response = client.get_datapipeline_packages(
                    pipeline_id=pipeline_id,
                    start_datetime=(
                        start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    ),
                    end_datetime=(
                        end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    ),
                    top=args.top
                )
                # Create a bundle file for this time interval
                bundle_name = (
                    f"bundle-"
                    f"{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                    f"-{end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}.gz"
                )
                bundle_path = output_path.joinpath(bundle_name)
                # Process all packages that were retrieved
                if packages_response["items"]:
                    with open(bundle_path, "wb") as fd:
                        for item in packages_response["items"]:
                            package_id = item["id"]
                            package = client.get_datapipeline_package(
                                pipeline_id=pipeline_id,
                                package_id=package_id
                            )
                            fd.write(package)
                            print(f"- saved package: {package_id}")
                    print(
                        f'captured packages until: '
                        f'{end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")}'
                    )
                    print(
                        f"  - captured package count: "
                        f"{len(packages_response['items'])}"
                    )
                    print(f"  - bundle path: {bundle_path}")
                else:
                    print(
                        f"No packages found in the time interval "
                        f"{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')} "
                        f"to {end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                    )
                # Update the time window for the next iteration
                start_datetime = end_datetime
                end_datetime = (
                    start_datetime + datetime.timedelta(seconds=interval)
                )
                process_start = time.time()
                print(
                    "  - next request is around: ",
                    end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                )
            time.sleep(3)
        print("Capture process terminated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Trend Vision One Data Pipeline Management Tool"
    )
    parser.add_argument(
        "-t",
        "--v1-token",
        default=V1_TOKEN,
        help="Authentication token of your Trend Vision One user account",
    )
    parser.add_argument(
        "-u",
        "--v1-url",
        default=V1_URL,
        help=(
            "URL of the Trend Micro One server for your region."
            f' The default value is "{TmV1Client.base_url_default}"'
        ),
    )
    parser.add_argument(
        "-f", "--token-file",
        help="Path to file containing the authentication token"
    )
    request_parsers = parser.add_subparsers(dest="request")
    register_parser = request_parsers.add_parser("register")
    register_parser.add_argument(
        "-t",
        "--type",
        choices=["telemetry", "detection"],
        required=True,
        help="Data pipeline type: telemetry or detection",
    )
    register_parser.add_argument("-d", "--description", default="")
    register_parser.add_argument(
        "-s",
        "--sub-type",
        action="append",
        choices=TmV1Client.telemetry_subtypes,
        help="Subtypes for telemetry data (can specify multiple)",
    )
    list_parser = request_parsers.add_parser("list")
    get_parser = request_parsers.add_parser("get")
    get_parser.add_argument("pipeline_id", help="Pipeline ID to get")
    update_parser = request_parsers.add_parser("update")
    update_parser.add_argument("pipeline_id", help="Pipeline ID to update")
    update_parser.add_argument(
        "-t", "--type",
        choices=["telemetry", "detection"],
        help="Data pipeline type"
    )
    update_parser.add_argument(
        "-s",
        "--sub-type",
        action="append",
        choices=TmV1Client.telemetry_subtypes,
        help="Subtypes for telemetry data (can specify multiple)",
    )
    update_parser.add_argument(
        "-d", "--description",
        help="Pipeline description"
    )
    delete_parser = request_parsers.add_parser("delete")
    delete_parser.add_argument(
        "pipeline_id",
        nargs="+",
        help="Pipeline ID(s) to delete"
    )
    list_packages_parser = request_parsers.add_parser("list-packages")
    list_packages_parser.add_argument("pipeline_id", help="Pipeline ID")
    list_packages_parser.add_argument(
        "-s", "--start-datetime", help="2022-09-15T14:10:00Z")
    list_packages_parser.add_argument(
        "-e", "--end-datetime", help="2022-09-15T14:30:00Z")
    list_packages_parser.add_argument(
        "-t", "--top", type=int,
        default=500, choices=TmV1Client.packages_top_choices,
        help="Maximum number of results to return")
    get_package_parser = request_parsers.add_parser("get-package")
    get_package_parser.add_argument("pipeline_id", help="Pipeline ID")
    get_package_parser.add_argument("package_id", help="Package ID")
    get_package_parser.add_argument("output", help="Output file path")
    cont_get_package_parser = request_parsers.add_parser(
        "continuous-get-packages",
        help="Continuously retrieve packages at regular intervals. "
             "To stop the process, press 'Ctrl+C'."
    )
    cont_get_package_parser.add_argument("pipeline_id", help="Pipeline ID")
    cont_get_package_parser.add_argument(
        "-v", "--interval", type=int, default=180,
        choices=TmV1Client.interval_choices,
        help="Interval in seconds between package retrievals")
    cont_get_package_parser.add_argument(
        "-t", "--top", type=int, default=500,
        choices=TmV1Client.packages_top_choices,
        help="Maximum number of results to return per request")
    cont_get_package_parser.add_argument(
        "output_dir",
        help="Output directory path"
    )
    _args = parser.parse_args()

    main(_args)
