import argparse
import datetime
import json
import pathlib
import logging
import uuid
import requests
import signal
import time
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
class OATPipeline:
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
        Displays all data pipelines that have registered users

        Returns:
            dict: JSON response from the API containing the list of data pipelines
        """
        api = '/v3.0/oat/dataPipelines'
        resp = self.session.get(self.endpoint_url.format(api=api), headers=self.get_headers())
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.json()
    
    def register_datapipeline(self, risk_levels, description):
        """
        Registers a customer to the Observed Attack Techniques data pipeline.

        Args:
            risk_levels (list): List of risk levels (e.g., ["critical", "high"])
            description (str): Description of the data pipeline
            has_detail (bool, optional): Whether to include details. Defaults to False.

        Returns:
            dict: JSON response from the API
        """

        api = '/v3.0/oat/dataPipelines'
        resp = self.session.post(self.endpoint_url.format(api=api), headers=self.get_headers(), json={
            "riskLevels": json.loads(risk_levels),
            "hasDetail": False,
            "description": description
        })
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.headers.get('Location')

    def get_datapipeline(self, pipeline_id):
        """
        Displays all data pipelines that have registered users

        Returns:
            dict: JSON response from the API containing the list of data pipelines
        """
        api = f'/v3.0/oat/dataPipelines/{pipeline_id}'
        resp = self.session.get(self.endpoint_url.format(api=api), headers=self.get_headers())
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.json()

    def modify_datapipeline(self, pipeline_id, risk_levels, description, has_detail=False, if_match=None):
        """
        Modifies the settings of the specified data pipeline
        
        Args:
            pipeline_id (str): The ID of the data pipeline to modify
            risk_levels (list): List of risk levels (e.g., ["critical", "high"])
            description (str): Description of the data pipeline
            has_detail (bool, optional): Whether to include details. Defaults to False.
            if_match (str, optional): ETag for concurrency control. Required by the API.
            
        Returns:
            dict: JSON response from the API
        """
        api = f"/v3.0/oat/dataPipelines/{pipeline_id}"
        
        if not pipeline_id:
            raise ValueError("Pipeline ID is required")
        
        headers = self.get_headers()
        if if_match:
            headers['If-Match'] = if_match
        else:
            # If-Match is required according to the documentation
            raise ValueError("If-Match header is required for modifying a data pipeline")
        
        # Ensure risk_levels is a list
        if isinstance(risk_levels, str):
            try:
                risk_levels = eval(risk_levels)
            except:
                risk_levels = [risk_levels]
        
        data = {
            "riskLevels": risk_levels,
            "hasDetail": has_detail,
            "description": description
        }
        
        resp = self.session.patch(
            self.endpoint_url.format(api=api.format(id=pipeline_id)), 
            headers=headers, 
            json=data
        )
        
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.json()
    


    def list_datapipeline_packages(self, pipeline_id, start_datetime, end_datetime, top=500, next_link=None):
        """
        Displays all the available packages from a data pipeline a paginated list.

        Args:
            pipeline_id (str): The ID of the data pipeline
            start_datetime (str, optional): Start time for filtering events (ISO format)
            end_datetime (str, optional): End time for filtering events (ISO format)
            top (int, optional): Maximum number of records to return
            
        Returns:
            dict: JSON response from the API containing the event packages
        """
        
        api = f'/v3.0/oat/dataPipelines/{pipeline_id}/packages'
        if next_link is None:
            resp = self.session.get(self.endpoint_url.format(api=api), headers=self.get_headers(), params={
                'startDateTime': start_datetime,
                'endDateTime': end_datetime,
                'top': top
            })
        else:
            resp = self.session.get(next_link, headers=self.get_headers())
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.json()

    def get_datapipeline_package(self, pipeline_id, package_id):
        """
        Retrieves the specified Observed Attack Techniques package

        Args:
            pipeline_id (str): The ID of the data pipeline
            package_id (str): The ID of the package to retrieve
            
        Returns:
            dict: JSON response from the API containing the package details   
        """
        api = f'/v3.0/oat/dataPipelines/{pipeline_id}/packages/{package_id}'
        resp = self.session.get(self.endpoint_url.format(api=api), headers=self.get_headers(), stream=True)
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.raw.read()

    def delete_datapipeline(self, pipeline_id_list):
        """
        Unregisters a customer from the Observed Attack Techniques data pipeline.
        
        Args:
            pipeline_ids (list): Provide the pipeline ID to delete
        
        Returns:
            dict: JSON response from the API
        """
        api = '/v3.0/oat/dataPipelines/delete'
        resp = self.session.post(self.endpoint_url.format(api=api), headers=self.get_headers(),
                                 json=[{'id': p} for p in pipeline_id_list])
        logger.info(f'resp={resp}, trace-id={resp.headers.get("x-trace-id")}')
        resp.raise_for_status()
        return resp.json()

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

    # print(f"Token starts with: {token[:10]}... (length: {len(token)})")
    
    dp = OATPipeline(url, token)

    if args.request == 'register':
        logger.info(f'request: {args.request}, args: risk_levels={args.risk_levels}, description={args.description}')

        result = dp.register_datapipeline(
            risk_levels=args.risk_levels, 
            description=args.description
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
                FirstRound = False
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
    else:
        logging.error(f"Unknown request: {args.request}")
    return 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url')
    parser.add_argument('-f', '--token-path')
    request_parsers = parser.add_subparsers(dest='request')

    register_parser = request_parsers.add_parser('register')
    register_parser.add_argument('-r', '--risk-levels', required=True, help='registered risk level. Ex: ["info", "low", "medium", "high", "critical"]')
    register_parser.add_argument('-d', '--description', default='')

    list_parser = request_parsers.add_parser('list')

    modify_parser = request_parsers.add_parser('modify')
    modify_parser.add_argument('-p', '--pipeline-id', required=True, help='ID of the pipeline to modify')
    modify_parser.add_argument('-r', '--risk-levels', required=True, help='Updated risk levels. Ex: ["info", "low", "medium", "high", "critical"]')
    modify_parser.add_argument('-d', '--description', required=True, help='Updated description')
    modify_parser.add_argument('--has-detail', action='store_true', help='Whether to include details')
    modify_parser.add_argument('-i', '--if-match', required=True, help='ETag for concurrency control')
    
    get_parser = request_parsers.add_parser('get')
    get_parser.add_argument('-p', '--pipeline-id', required=True)

    delete_parser = request_parsers.add_parser('delete')
    delete_parser.add_argument('-p', '--pipeline-id', action='append', required=True)

    list_packages_parser = request_parsers.add_parser('list-packages')
    list_packages_parser.add_argument('-p', '--pipeline-id', required=True)
    list_packages_parser.add_argument('-s', '--start-datetime', help='2022-09-15T14:10:00Z')
    list_packages_parser.add_argument('-e', '--end-datetime', help='2022-09-15T14:30:00Z')
    list_packages_parser.add_argument('-t', '--top', default=500, help='2022-09-15T14:30:00Z')
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
