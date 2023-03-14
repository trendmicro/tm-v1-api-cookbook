import argparse
import datetime
import getpass
import json
import os
import re

import requests
import taxii2client.v20
import taxii2client.v21

# default settings
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
TAXII_URL = os.environ.get('TMV1_TAXII_URL', '')
TAXII_USER = os.environ.get('TMV1_TAXII_USER')
TAXII_PASSWORD = os.environ.get('TMV1_TAXII_PASSWORD')


class TmV1Client:
    base_url_default = V1_URL

    def __init__(self, token, base_url=None):
        if not token:
            raise ValueError('Authentication token missing')
        self.token = token
        self.base_url = base_url or TmV1Client.base_url_default

    def make_headers(self):
        return {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json;charset=utf-8'
        }

    def post(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.post(self.base_url + path, **kwargs)
        if ((200 == r.status_code)
                and ('application/json' in r.headers.get('Content-Type', ''))):
            return r.json()
        raise RuntimeError(f'Request unsuccessful (POST {path}):'
                           f' {r.status_code} {r.text}')

    def get_query_length_limit(self, start, end):
        CONTENT_LENGTH_LIMIT = 100000
        body = {
            'fields': [],
            'from': int(start.timestamp()),
            'to': int(end.timestamp()),
            'source': 'endpointActivityData'}
        return CONTENT_LENGTH_LIMIT - len(json.dumps(body))

    def search_endpont_activity(self, start, end, query):
        return self.post('/v2.0/xdr/search/data', json={
            'fields': [],
            'from': int(start.timestamp()),
            'to': int(end.timestamp()),
            'source': 'endpointActivityData',
            'query': query})


def extract_iocs_from_stix_objects(objects):
    if not objects:
        return {}

    domain_pattern = re.compile(r"domain-name:value = '(\S+)'")
    url_pattern = re.compile(r"url:value = '(\S+)'")
    ipv4_pattern = re.compile(r"ipv4-addr:value = '(\S+)'")
    ipv6_pattern = re.compile(r"ipv6-addr:value = '(\S+)'")
    sha1_pattern = re.compile(r"file:hashes.'SHA-1' = '(\S+)'")

    iocs = {'domain': [], 'url': [], 'ipaddr': [], 'sha1': []}
    for object in objects:
        if object['type'] == 'indicator':
            ioc_pattern = object['pattern']
            iocs['domain'].extend(domain_pattern.findall(ioc_pattern))
            iocs['url'].extend(url_pattern.findall(ioc_pattern))
            iocs['ipaddr'].extend(ipv4_pattern.findall(ioc_pattern))
            iocs['ipaddr'].extend(ipv6_pattern.findall(ioc_pattern))
            iocs['sha1'].extend(sha1_pattern.findall(ioc_pattern))
    return iocs


def fetch_iocs_from_taxii(url, user, password, version):
    if version == '2.0':
        server = taxii2client.v20.Server(url, user=user, password=password)
        as_pages = taxii2client.v20.as_pages
    elif version == '2.1':
        server = taxii2client.v21.Server(url, user=user, password=password)
        as_pages = taxii2client.v21.as_pages
    else:
        raise RuntimeError(f'Unsupported TAXII server version: {version}')

    objects = []
    for collection in server.default.collections:
        if not collection.can_read:
            continue
        for envelope in as_pages(collection.get_objects, per_request=50):
            objects.extend(envelope['objects'])
            print('\rSTIX objects retrieved from TAXII server:'
                  f' {len(objects)}', end=(''))
    print('')
    return extract_iocs_from_stix_objects(objects)


def generate_search_query(iocs, length_limit):
    SEARCH_FIELDS = {
        'domain': ['request', 'hostName'],
        'url': ['request'],
        'ipaddr': ['request', 'objectIp', 'objectIps'],
        'sha1': [
            'objectFileHashSha1', 'parentFileHashSha1', 'processFileHashSha1']}
    current_query = ''
    for ioc_type, ioc_values in iocs.items():
        search_fields = SEARCH_FIELDS[ioc_type]
        for ioc_value in ioc_values:
            for search_field in search_fields:
                or_op = ' OR ' if current_query else ''
                new_query = f'{or_op}{search_field}:"{ioc_value}"'
                if (len(current_query) + len(new_query)) < length_limit:
                    current_query += new_query
                else:
                    yield current_query
                    new_query = f'{search_field}:"{ioc_value}"'
                    current_query = new_query
    yield current_query


def merge_search_results(dest, src):
    if not isinstance(dest, dict):
        return
    if not dest:
        dest.update(src)
        return
    dest_data = dest['data']
    dest_logs = dest_data['logs']
    src_logs = src['data']['logs']
    dest_logs.extend([log for log in src_logs if log not in dest_logs])
    dest_logs.sort(key=lambda log: log['eventTime'], reverse=True)
    dest_data['total_count'] = len(dest_logs)


def search_iocs_for_endpoints(start, end, token, url, iocs):
    v1 = TmV1Client(token, url)
    search_results = {}
    query_length_limit = v1.get_query_length_limit(start, end)
    for search_query in generate_search_query(iocs, query_length_limit):
        search_result = v1.search_endpont_activity(start, end, search_query)
        merge_search_results(search_results, search_result)
    return search_results


def main(start, end, days, v1_token, v1_url,
         taxii_url, taxii_user, taxii_password, taxii_version):
    if end is None:
        end = datetime.datetime.now(datetime.timezone.utc)
    else:
        end = datetime.datetime.fromisoformat(end)
    if start is None:
        start = end + datetime.timedelta(days=-days)
    else:
        start = datetime.datetime.fromisoformat(start)

    if taxii_user:
        if not taxii_password:
            taxii_password = getpass.getpass()
    iocs = fetch_iocs_from_taxii(taxii_url, taxii_user, taxii_password,
                                 taxii_version)
    if iocs:
        print('')
        print('IoCs extracted from STIX objects:')
        print(json.dumps(iocs, indent=2))
        print('')
        search_results = search_iocs_for_endpoints(
            start, end, v1_token, v1_url, iocs)
        print('IoC instances found in endpoint activity data:')
        print(json.dumps(search_results, indent=2))
    else:
        print('No IoCs found in STIX objects')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Perform threat hunting based on IoCs from a source',
        epilog=(f'Example: python {os.path.basename(__file__)} '
                '-e 2021-04-12T14:28:00.123456+00:00 -d 5'))
    parser.add_argument(
        '-s', '--start',
        help=('Timestamp in ISO 8601 format that indicates the start of'
              ' the data retrieval time range'))
    parser.add_argument(
        '-e', '--end',
        help=('Timestamp in ISO 8601 format that indicates the end of the data'
              ' retrieval time range. The default value is the current time.'))
    parser.add_argument(
        '-d', '--days', type=int, default=5,
        help=('Number of days before the end time of the data retrieval'
              ' time range. The default value is 5.'))
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help='Authentication token of your Trend Vision One user account')
    parser.add_argument(
        '-r', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    parser.add_argument(
        '-R', '--taxii-url', default=TAXII_URL,
        help='URL of the TAXII server')
    parser.add_argument(
        '-u', '--taxii-user', default=TAXII_USER,
        help='Username associated with the TAXII server')
    parser.add_argument(
        '-p', '--taxii-password', default=TAXII_PASSWORD,
        help='Password for the TAXII server')
    parser.add_argument(
        '-v', '--taxii-version', default='2.1', choices=['2.0', '2.1'],
        help='Version of the TAXII server. The default value is 2.1.')
    main(**vars(parser.parse_args()))
