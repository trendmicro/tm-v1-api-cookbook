import argparse
import datetime
import logging
import json
import pathlib
import uuid
import signal
import time

import requests

from pathlib import Path

from requests.adapters import HTTPAdapter
from urllib3.util import Retry


logging.basicConfig(
    filename=f'{Path(__file__).name.replace(".py", "")}.log',
    format='%(asctime)s [%(levelname)s][%(funcName)s][%(lineno)d] %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

# class to interact with data pipeline APIs
class DatalakePipeline:
    def __init__(self, endpoint_url, jwt):
        self.endpoint_url = endpoint_url + '{api}'
        self.jwt = jwt
        self.session = requests.Session()
        retry = Retry(total=5, status_forcelist=[429, 502, 504], allowed_methods=['GET'], backoff_factor=1)
        http_adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('https://', http_adapter)

    def get_headers(self):
        return {'x-trace-id': str(uuid.uuid4()), 'x-task-id': str(uuid.uuid4()), 'Authorization': f'Bearer {self.jwt}'}

    def list_datapipelines(self):
        """
        Displays all data pipelines that have a data type assigned.

        Returns:
            dict: The response JSON containing all data pipelines
        """
        api = '/v3.0/datalake/dataPipelines'
        resp = self.session.get(self.endpoint_url.format(api=api), headers=self.get_headers())
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
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
        api = '/v3.0/datalake/dataPipelines'
        payload = {
            'type': data_type,
            'description': description
        }
        
        if sub_type:
            payload['subType'] = sub_type
            
        resp = self.session.post(
            self.endpoint_url.format(api=api), 
            headers=self.get_headers(), 
            json=payload
        )
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            print(f"Response content: {resp.text}") 
        return resp.headers.get('Location')

    def get_datapipeline(self, pipeline_id):
        """
        Displays information about the specified data pipeline.
        
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
            
        Returns:
            dict: The response JSON containing pipeline details
        """
        api = f'/v3.0/datalake/dataPipelines/{pipeline_id}'
        resp = self.session.get(self.endpoint_url.format(api=api), headers=self.get_headers())
        try:
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            if resp.status_code == 404:
                print(f"Pipeline with ID {pipeline_id} not found. It may have been deleted or never existed.")
                return None
            else:
                print(f"Error retrieving pipeline: {err}")
                return None

    def update_datapipeline(self, pipeline_id, data_type=None, sub_type=None, description=None):
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
        api = f'/v3.0/datalake/dataPipelines/{pipeline_id}'
                
        request_body = {}
        if data_type is not None:
            request_body['type'] = data_type
        if sub_type is not None:
            request_body['subType'] = sub_type
        if description is not None:
            request_body['description'] = description
        
        resp = self.session.patch(
            self.endpoint_url.format(api=api),
            headers=self.get_headers(),
            json=request_body
        )
        
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        print(f'Status Code: {resp.status_code}, Response Text: {resp.text}, trace-id={resp.headers.get("x-trace-id")}')
        try:
            return resp.json()
        except ValueError as e:
            logger.error(f'Error decoding JSON: {e}')
            logger.error(f'Response Text: {resp.text}')
            return None 

    def list_datapipeline_packages(self, pipeline_id, start_datetime, end_datetime, top=500, next_link=None):
        """
        Display all the available packages from a data pipeline a paginated list.
        
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
            start_datetime (str): Start date/time for package search
            end_datetime (str): End date/time for package search
            top (int, optional): Maximum number of results to return
            next_link (str, optional): URL for the next page of results
            
        Returns:
            dict: The response JSON containing package information
        """
        api = f'/v3.0/datalake/dataPipelines/{pipeline_id}/packages'
        if next_link is None:
            resp = self.session.get(
                self.endpoint_url.format(api=api), 
                headers=self.get_headers(), 
                params={
                    'startDateTime': start_datetime,
                    'endDateTime': end_datetime,
                    'top': top
                }
            )
        else:
            resp = self.session.get(next_link, headers=self.get_headers())
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.json()

    def get_datapipeline_package(self, pipeline_id, package_id):
        """
        Retrieve the specified data pipeline package.
        
        Args:
            pipeline_id (str): Unique identifier for the data pipeline
            package_id (str): Unique identifier for the package
            
        Returns:
            bytes: The raw package data
        """
        api = f'/v3.0/datalake/dataPipelines/{pipeline_id}/packages/{package_id}'
        resp = self.session.get(
            self.endpoint_url.format(api=api), 
            headers=self.get_headers(), 
            stream=True
        )
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.raw.read()

    def delete_datapipeline(self, pipeline_id_list):
        """
        Unbind data type from pipeline(s)
        
        Args:
            pipeline_id_list (list): List of pipeline IDs to delete
            
        Returns:
            list: A list containing a single dictionary with status code and message
        """
        api = '/v3.0/datalake/dataPipelines/delete'
        resp = self.session.post(
            self.endpoint_url.format(api=api), 
            headers=self.get_headers(),
            json=[{'id': p} for p in pipeline_id_list]
        )
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return [{"status": resp.status_code, "message": "Pipeline(s) successfully deleted"}]


# SIGINT handler to stop continuous-get-packages
def signal_int_handler(sig, frame):
    print('stop capturing')
    global CAPTURING
    CAPTURING = False


# flag to indicate if continue in continuous-get-packages mode
CAPTURING = True


def main(args):
    url = args.url
    with open(args.token_path) as fd:
        token = fd.read().strip()

    dp = DatalakePipeline(url, token)

    if args.request == 'register':
        logger.info(f'request: {args.request}, args: type={args.type}, description={args.description}')
        result = dp.register_datapipeline(
            data_type=args.type,
            description=args.description,
            sub_type=args.sub_type
        )
        print(result)

    elif args.request == 'list':
        logger.info(f'request: {args.request}')
        result = dp.list_datapipelines()
        print(json.dumps(result, indent=2))

    elif args.request == 'get':
        logger.info(f'request: {args.request}, args: pipeline_id={args.pipeline_id}')
        result = dp.get_datapipeline(pipeline_id=args.pipeline_id)
        print(json.dumps(result, indent=2))

    elif args.request == 'update':
        logger.info(f'request: {args.request}, args: pipeline_id={args.pipeline_id}, type={args.type}, sub_type={args.sub_type}, description={args.description}')
        result = dp.update_datapipeline(
            pipeline_id=args.pipeline_id,
            data_type=args.type,
            sub_type=args.sub_type,
            description=args.description
        )
        print(json.dumps(result, indent=2))

    elif args.request == 'delete':
        logger.info(f'request: {args.request}, args: pipeline_id_list={args.pipeline_id}')
        result = dp.delete_datapipeline(pipeline_id_list=args.pipeline_id)
        print(json.dumps(result, indent=2))

    elif args.request == 'list-packages':
        logger.info(f'request: {args.request}, args: pipeline_id={args.pipeline_id}, start_datetime={args.start_datetime}, end_datetime={args.end_datetime}, top={args.top}, next_link={args.next_link}')
        result = dp.list_datapipeline_packages(
            pipeline_id=args.pipeline_id, 
            start_datetime=args.start_datetime,
            end_datetime=args.end_datetime, 
            top=args.top, 
            next_link=args.next_link
        )
        print(json.dumps(result, indent=2))

    elif args.request == 'get-package':
        logger.info(f'request: {args.request}, args: pipeline_id={args.pipeline_id}, package_id={args.package_id}, output={args.output}')
        output_path = pathlib.Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = dp.get_datapipeline_package(
            pipeline_id=args.pipeline_id, 
            package_id=args.package_id
        )
        with open(output_path, 'wb') as fd:
            fd.write(result)

    elif args.request == 'continuous-get-packages':
        output_path = pathlib.Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        signal.signal(signal.SIGINT, signal_int_handler)

        interval = args.interval
        pipeline_id = args.pipeline_id

        start_datetime = datetime.datetime.now(tz=datetime.timezone.utc)
        end_datetime = start_datetime + datetime.timedelta(seconds=interval)
        process_start = time.time()
        print('start capturing..., next request is around: ', end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'))

        while CAPTURING:
            if time.time() - process_start > interval:
                list_args = {
                    'pipeline_id': pipeline_id,
                    'start_datetime': start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'end_datetime': end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                idx = 0
                while True:
                    bundle_name = f"bundle-{start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}-{end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}-{idx}.gz"
                    bundle_path = output_path.joinpath(bundle_name)
                    page = dp.list_datapipeline_packages(**list_args)

                    if page['items']:
                        with open(bundle_path, 'wb') as fd:
                            for item in page['items']:
                                package_id = item['id']
                                package = dp.get_datapipeline_package(pipeline_id=pipeline_id, package_id=package_id)
                                fd.write(package)
                                logger.info(f'- saved package: {package_id}')
                        logger.info(f'captured packages until: {end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")}')
                        logger.info(f'  - captured package count: {len(page["items"])}')
                        logger.info(f'  - bundle path: {bundle_path}')

                    next_link = page.get('nextLink')
                    if next_link:
                        list_args = {'next_link': next_link}
                        idx += 1
                    else:
                        break

                start_datetime = end_datetime
                end_datetime = start_datetime + datetime.timedelta(seconds=interval)

                process_start = time.time()
                print('  - next request is around: ', end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ'))
            time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url')
    parser.add_argument('-f', '--token-path')
    request_parsers = parser.add_subparsers(dest='request')

    register_parser = request_parsers.add_parser('register')
    register_parser.add_argument('-t', '--type', choices=['telemetry', 'detection'], required=True, help='data pipeline type: telemetry or detection')
    register_parser.add_argument('-d', '--description', default='')
    register_parser.add_argument('-s', '--sub-type', action='append', help='Subtypes for telemetry data (can specify multiple)')

    list_parser = request_parsers.add_parser('list')

    get_parser = request_parsers.add_parser('get')
    get_parser.add_argument('-p', '--pipeline-id', required=True)
    
    update_parser = request_parsers.add_parser('update')
    update_parser.add_argument('-p', '--pipeline-id', required=True, help='Pipeline ID to update')
    update_parser.add_argument('-t', '--type', choices=['telemetry', 'detection'], help='Data pipeline type')
    update_parser.add_argument('-s', '--sub-type', action='append', help='Subtypes for telemetry data (can specify multiple)')
    update_parser.add_argument('-d', '--description', help='Pipeline description')

    delete_parser = request_parsers.add_parser('delete')
    delete_parser.add_argument('-p', '--pipeline-id', action='append', required=True)

    list_packages_parser = request_parsers.add_parser('list-packages')
    list_packages_parser.add_argument('-p', '--pipeline-id', required=True)
    list_packages_parser.add_argument('-s', '--start-datetime', help='2022-09-15T14:10:00Z')
    list_packages_parser.add_argument('-e', '--end-datetime', help='2022-09-15T14:30:00Z')
    list_packages_parser.add_argument('-t', '--top',type=int ,default=500, help='2022-09-15T14:30:00Z')
    list_packages_parser.add_argument('-l', '--next-link', help='nextLink from previous response for list next page')

    get_package_parser = request_parsers.add_parser('get-package')
    get_package_parser.add_argument('-p', '--pipeline-id', required=True)
    get_package_parser.add_argument('-k', '--package-id', required=True)
    get_package_parser.add_argument('-o', '--output', required=True)

    cont_get_package_parser = request_parsers.add_parser('continuous-get-packages')
    cont_get_package_parser.add_argument('-p', '--pipeline-id', required=True)
    cont_get_package_parser.add_argument('-v', '--interval', type=int, default=180)
    cont_get_package_parser.add_argument('-t', '--top', type=int, default=500)
    cont_get_package_parser.add_argument('-o', '--output-dir', required=True)

    _args = parser.parse_args()

    main(_args)
