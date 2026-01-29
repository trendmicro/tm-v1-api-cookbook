import argparse
import datetime
import json
import os
import pathlib
import signal
import time
import uuid
from pathlib import Path
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


# Standard environment variables
V1_TOKEN = os.environ.get("TMV1_TOKEN", "")
# Specify the correct domain name for your region in V1_URL
#   default: https://api.xdr.trendmicro.com (US region)
V1_URL = os.environ.get("TMV1_URL", "https://api.xdr.trendmicro.com")
# This value is used for User-Agent header in API requests
V1_UA = os.environ.get(
    "TMV1_UA", f"Trend Vision One API Cookbook ({os.path.basename(__file__)})"
)


class TmV1Client:
    base_url_default = V1_URL

    def __init__(self, token, base_url=None):
        if not token:
            raise ValueError("Authentication token missing")
        self.endpoint_url = base_url + "{api}"
        self.jwt = token
        self.user_agent = V1_UA
        self.session = Session()
        retry = Retry(
            total=5,
            status_forcelist=[429, 502, 504],
            allowed_methods=["GET"],
            backoff_factor=1,
        )
        http_adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", http_adapter)

    def get_headers(self):
        """
        Get headers for API requests including authentication.
        Returns:
            dict: Headers with trace ID, task ID, and authorization token.
        """
        return {
            "x-trace-id": str(uuid.uuid4()),
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
            if next_link is None:
                resp = self.session.get(
                    self.endpoint_url.format(api=api_path),
                    headers=self.get_headers(),
                    **kwargs
                )
            else:
                resp = self.session.get(next_link, headers=self.get_headers())
            print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
            if resp.status_code != 200:
                raise RuntimeError(
                    f'Request unsuccessful (GET {api_path}): '
                    f'{resp.status_code} {resp.text}'
                )
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
        Displays all data pipelines that have registered users
        Returns:
            dict: JSON response containing the list of data pipelines
        """
        api = "/v3.0/oat/dataPipelines"
        resp = self.session.get(
            self.endpoint_url.format(api=api), headers=self.get_headers()
        )
        print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        if resp.status_code != 200:
            raise RuntimeError(
                f"Request unsuccessful ({resp.request.method} "
                f"{resp.url}): {resp.status_code} {resp.text}"
            )
        return resp.json()

    def register_datapipeline(self, risk_levels, description):
        """
        Registers a customer to the Observed Attack Techniques data pipeline.
        Args:
            risk_levels (list): List of risk levels
            description (str): Description of the data pipeline
            has_detail (bool, optional): Whether to include details.
                                         Defaults to False.
        Returns:
            dict: JSON response from the API
        """
        api = "/v3.0/oat/dataPipelines"
        resp = self.session.post(
            self.endpoint_url.format(api=api),
            headers=self.get_headers(),
            json={
                "riskLevels": json.loads(risk_levels),
                "hasDetail": False,
                "description": description,
            },
        )
        print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        if resp.status_code not in [200, 201]:
            raise RuntimeError(
                f"Request unsuccessful"
                f" ({resp.request.method} {resp.url}): "
                f"{resp.status_code} {resp.text}"
            )
        return resp.headers.get("Location")

    def get_datapipeline(self, pipeline_id):
        """
        Displays all data pipelines that have registered users
        Args:
            pipeline_id (str): The ID of the data pipeline
        Returns:
            dict: JSON response
                  from the API containing the list of data pipelines
        """
        api = f"/v3.0/oat/dataPipelines/{pipeline_id}"
        resp = self.session.get(
            self.endpoint_url.format(api=api), headers=self.get_headers()
        )
        print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        if resp.status_code != 200:
            raise RuntimeError(
                f"Request unsuccessful "
                f"({resp.request.method} {resp.url}): "
                f"{resp.status_code} {resp.text}"
            )
        return resp.json()

    def update_datapipeline(
        self, pipeline_id, risk_levels,
        description, has_detail=False, if_match=None
    ):
        """
        Modifies the settings of the specified data pipeline
        Args:
            pipeline_id (str): The ID of the data pipeline to modify.
            risk_levels (list): List of risk levels.
            description (str): Description of the data pipeline.
            has_detail (bool, optional): Whether to include details.
            if_match (str, optional): ETag for concurrency control.
        Returns:
            dict: JSON response from the API
        """
        api = f"/v3.0/oat/dataPipelines/{pipeline_id}"
        if not pipeline_id:
            raise ValueError("Pipeline ID is required")
        headers = self.get_headers()
        if if_match:
            headers["If-Match"] = if_match
        else:
            # If-Match is required according to the documentation
            raise ValueError(
                "If-Match header is required for modifying a data pipeline"
            )
        # Ensure risk_levels is a list
        if isinstance(risk_levels, str):
            try:
                risk_levels = eval(risk_levels)
            except Exception as e:
                raise ValueError(f"Invalid risk_levels format: {e}") from e
        data = {
            "riskLevels": risk_levels,
            "hasDetail": has_detail,
            "description": description,
        }
        resp = self.session.patch(
            self.endpoint_url.format(api=api), headers=headers, json=data
        )
        print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        if resp.status_code != 200:
            raise RuntimeError(
                f"Request unsuccessful "
                f"({resp.request.method} {resp.url}): "
                f"{resp.status_code} {resp.text}"
            )
        return resp.json()

    def get_datapipeline_packages(
        self, pipeline_id, start_datetime, end_datetime,
        top=500, next_link=None
    ):
        """
        Displays all the available packages from a data pipeline paginated list
        Args:
            pipeline_id (str): The ID of the data pipeline
            start_datetime (str, optional): Start time for filtering events
            end_datetime (str, optional): End time for filtering events
            top (int, optional): Maximum number of records to return
        Returns:
            dict: JSON response from the API containing the event packages
        """
        api = f"/v3.0/oat/dataPipelines/{pipeline_id}/packages"
        params = {
            "startDateTime": start_datetime,
            "endDateTime": end_datetime,
            "top": top,
        }
        return self.get_items(api, params=params)

    def get_datapipeline_package(self, pipeline_id, package_id):
        """
        Retrieves the specified Observed Attack Techniques package
        Args:
            pipeline_id (str): The ID of the data pipeline
            package_id (str): The ID of the package to retrieve
        Returns:
            dict: JSON response from the API containing the package details
        """
        api = f"/v3.0/oat/dataPipelines/{pipeline_id}/packages/{package_id}"
        resp = self.session.get(
            self.endpoint_url.format(api=api),
            headers=self.get_headers(), stream=True
        )
        print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        if resp.status_code != 200:
            raise RuntimeError(
                f"Request unsuccessful "
                f"({resp.request.method} {resp.url}): "
                f"{resp.status_code} {resp.text}"
            )
        return resp.raw.read()

    def delete_datapipeline(self, pipeline_id_list):
        """
        Unregisters a customer from the OAT data pipeline.
        Args:
            pipeline_ids (list): Provide the pipeline ID to delete
        Returns:
            dict: JSON response from the API
        """
        api = "/v3.0/oat/dataPipelines/delete"
        resp = self.session.post(
            self.endpoint_url.format(api=api),
            headers=self.get_headers(),
            json=[{"id": p} for p in pipeline_id_list],
        )
        print(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        if resp.status_code != 200:
            raise RuntimeError(
                f"Request unsuccessful"
                f"({resp.request.method} {resp.url}):"
                f"{resp.status_code} {resp.text}"
            )
        return resp.json()


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
    url = args.url if args.url else V1_URL
    if args.token_path:
        with open(args.token_path) as fd:
            token = fd.read().strip()
    elif V1_TOKEN:
        token = V1_TOKEN
    else:
        raise ValueError("Authentication token missing")
    client = TmV1Client(token, url)
    if args.request == "register":
        print(
            f"request: {args.request}, "
            f"args: risk_levels={args.risk_levels}, "
            f"description={args.description}"
        )
        result = client.register_datapipeline(
            risk_levels=args.risk_levels, description=args.description
        )
        print(result)
    elif args.request == "list":
        print(f"request: {args.request}")
        result = client.get_datapipelines()
        print(json.dumps(result, indent=2))
    elif args.request == "get":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id={args.pipeline_id}"
        )
        result = client.get_datapipeline(pipeline_id=args.pipeline_id)
        print(json.dumps(result, indent=2))
    elif args.request == "update":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id={args.pipeline_id}, "
            f"risk_levels={args.risk_levels}, "
            f"description={args.description}, "
            f"has_detail={args.has_detail}, "
            f"if_match={args.if_match}"
        )
        result = client.update_datapipeline(
            pipeline_id=args.pipeline_id,
            risk_levels=args.risk_levels,
            description=args.description,
            has_detail=args.has_detail,
            if_match=args.if_match
        )
        print(json.dumps(result, indent=2))
    elif args.request == "delete":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id_list={args.pipeline_id}"
        )
        result = client.delete_datapipeline(pipeline_id_list=args.pipeline_id)
        print(json.dumps(result, indent=2))
    elif args.request == "list-packages":
        print(
            f"request: {args.request}, args: "
            f"pipeline_id={args.pipeline_id}, "
            f"start_datetime={args.start_datetime}, "
            f"end_datetime={args.end_datetime}, "
            f"top={args.top}, next_link={args.next_link}"
        )
        result = client.get_datapipeline_packages(
            pipeline_id=args.pipeline_id,
            start_datetime=args.start_datetime,
            end_datetime=args.end_datetime,
            top=args.top,
            next_link=args.next_link,
        )
        print(json.dumps(result, indent=2))
    elif args.request == "get-package":
        print(
            f"request: {args.request}, "
            f"args: pipeline_id={args.pipeline_id}, "
            f"package_id={args.package_id}, "
            f"output={args.output}"
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
        if hasattr(args, 'batch_size'):
            max_items_batch = args.batch_size
        else:
            max_items_batch = 100
        start_datetime = datetime.datetime.now(tz=datetime.timezone.utc)
        end_datetime = start_datetime + datetime.timedelta(seconds=interval)
        process_start = time.time()
        print(
            "start capturing..., next request is around: ",
            end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        while CAPTURING:
            if time.time() - process_start > interval:
                start_time_str = (
                    start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                end_time_str = (
                    end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                print(
                    f"Fetching packages for time window: "
                    f"{start_time_str} to {end_time_str}"
                )
                pkg_response = client.get_datapipeline_packages(
                    pipeline_id=pipeline_id,
                    start_datetime=start_time_str,
                    end_datetime=end_time_str,
                    top=args.top
                )
                total_packages = len(pkg_response["items"])
                print(f"Found {total_packages} packages to process")

                for batch_idx in range(0, total_packages, max_items_batch):
                    batch_end = min(
                        batch_idx + max_items_batch,
                        total_packages
                    )
                    bundle_name = (
                        f"bundle-{start_time_str}-{end_time_str}"
                        f"-batch{batch_idx}-{batch_end}.gz"
                    )
                    bundle_path = output_path.joinpath(bundle_name)
                    # Process this batch of packages
                    batch_items = (
                        pkg_response["items"][batch_idx:batch_end]
                    )
                    if batch_items:
                        print(
                            f"Processing batch "
                            f"{batch_idx}-{batch_end} "
                            f"of {total_packages} packages"
                        )
                        successful_packages = 0
                        with open(bundle_path, "wb") as fd:
                            for item in batch_items:
                                package_id = item["id"]
                                # Download the package
                                package = (client.get_datapipeline_package(
                                    pipeline_id=pipeline_id,
                                    package_id=package_id
                                ))
                                fd.write(package)
                                successful_packages += 1
                                print(
                                    f"- saved package: "
                                    f"{package_id}"
                                )
                        print(
                            f"Batch complete: {successful_packages}"
                            f"successful packages"
                        )
                        print(f"Saved to bundle: {bundle_path}")
                start_datetime = end_datetime
                end_datetime = (
                    start_datetime + datetime.timedelta(seconds=interval)
                )
                process_start = time.time()
                print(
                    f"Next time window: "
                    f"{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')} "
                    f"to {end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                )
            time.sleep(3)
        print("Capture process terminated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url")
    parser.add_argument("-f", "--token-path")
    request_parsers = parser.add_subparsers(dest="request")
    register_parser = request_parsers.add_parser("register")
    register_parser.add_argument(
        "risk_levels",
        help=(
            f'Registered risk level. '
            f'Ex: ["info", "low", "medium", "high", "critical"]'
        )
    )
    register_parser.add_argument("-d", "--description", default="")
    list_parser = request_parsers.add_parser("list")
    modify_parser = request_parsers.add_parser("update")
    modify_parser.add_argument(
        "pipeline_id",
        help="ID of the pipeline to modify"
    )
    modify_parser.add_argument(
        "risk_levels",
        help=(
            f'Updated risk levels. '
            f'Ex: ["info", "low", "medium", "high", "critical"]'
        )
    )
    modify_parser.add_argument(
        "description",
        help="Updated description"
    )
    modify_parser.add_argument(
        "--has-detail", action="store_true",
        help="Whether to include details"
    )
    modify_parser.add_argument(
        "if_match",
        help="ETag for concurrency control"
    )
    get_parser = request_parsers.add_parser("get")
    get_parser.add_argument("pipeline_id", help="Pipeline ID to get")
    delete_parser = request_parsers.add_parser("delete")
    delete_parser.add_argument(
        "pipeline_id",
        nargs="+",
        help="Pipeline ID(s) to delete"
    )
    list_packages_parser = request_parsers.add_parser("list-packages")
    list_packages_parser.add_argument("pipeline_id", help="Pipeline ID")
    list_packages_parser.add_argument(
        "-s", "--start-datetime", help="2022-09-15T14:10:00Z"
    )
    list_packages_parser.add_argument(
        "-e", "--end-datetime", help="2022-09-15T14:30:00Z"
    )
    list_packages_parser.add_argument(
        "-t", "--top", default=500,
        help="Maximum number of results to return"
    )
    list_packages_parser.add_argument(
        "-l", "--next-link",
        help="nextLink from previous response for list next page"
    )
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
        "-v", "--interval",
        type=int, default=180
    )
    cont_get_package_parser.add_argument(
        "-t", "--top",
        type=int, default=500
    )
    cont_get_package_parser.add_argument(
        "output_dir",
        help="Output directory path"
    )
    cont_get_package_parser.add_argument(
        "-b", "--batch-size",
        type=int, default=100,
        help="Maximum number of packages to process in a single batch"
    )
    _args = parser.parse_args()
    main(_args)
