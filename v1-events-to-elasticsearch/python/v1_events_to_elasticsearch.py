import datetime
import argparse
import os
import urllib.parse
import ssl
import getpass

import requests
import elasticsearch
import elasticsearch.helpers

# Setting variables
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
# Specify the correct domain name for your region in V1_URL
#   ref: https://automation.trendmicro.com/xdr/Guides/Regional-Domains
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
# This value is used for User-Agent header in API requests. So you can
# customize this value to describe your company name, integration tool name,
# and other values as you like.
#   default: "Trend Vision One API Cookbook ({script_name})"
V1_UA = os.environ.get('TMV1_UA', 'Trend Vision One API Cookbook '
                       f'({os.path.basename(__file__)})')
ES_URL = os.environ.get('TMV1_ELASTICSEARCH_URL', 'http://localhost:9200')
ES_INDEX_PREFIX = os.environ.get('TMV1_ELASTICSEARCH_INDEX_PREFIX', 'tmv1_')
ES_USER = os.environ.get('TMV1_ELASTICSEARCH_USER')
ES_PASSWORD = os.environ.get('TMV1_ELASTICSEARCH_PASSWORD')
ES_CAFILE = os.environ.get('TMV1_ELASTICSEARCH_CAFILE')
ES_CAPATH = os.environ.get('TMV1_ELASTICSEARCH_CAPATH')
ES_CERTFILE = os.environ.get('TMV1_ELASTICSEARCH_CERTFILE')
ES_KEYFILE = os.environ.get('TMV1_ELASTICSEARCH_KEYFILE')


def is_aware_datetime(d):
    return (d.tzinfo is not None) and (d.tzinfo.utcoffset(d) is not None)


def get_datetime_param(d):
    if not is_aware_datetime(d):
        d = d.astimezone()
    d = d.astimezone(datetime.timezone.utc)
    d = d.isoformat(timespec='seconds').replace('+00:00', 'Z')
    return d


class TmV1Client:
    base_url_default = V1_URL
    oat_top = [50, 100, 200]
    search_top = [50, 100, 500, 1000, 5000]
    audit_logs_top = [50, 100, 200]

    def __init__(self, token, base_url=None):
        if not token:
            raise ValueError('Authentication token missing')
        self.token = token
        self.base_url = base_url or TmV1Client.base_url_default

    def make_headers(self, **kwargs):
        headers = {}
        use_token = kwargs.pop('use_token', True)
        if use_token:
            headers['Authorization'] = 'Bearer ' + self.token
        if 'files' not in kwargs:
            headers['Content-Type'] = 'application/json;charset=utf-8'
        headers['User-Agent'] = V1_UA
        return headers

    def get(self, url_or_path, use_token=True, **kwargs):
        kwargs.setdefault('headers', {}).update(
            self.make_headers(use_token=use_token)
        )
        url = (self.base_url + url_or_path if url_or_path.startswith('/') else
               url_or_path)
        r = requests.get(url, **kwargs)
        if 200 == r.status_code:
            if 'application/json' in r.headers.get('Content-Type', ''):
                return r.json()
            return r.content
        raise RuntimeError(f'Request unsuccessful (GET {url_or_path}):'
                           f' {r.status_code} {r.text}')

    def get_items(self, path, **kwargs):
        items = []
        next_link = None
        while True:
            if next_link is None:
                r = self.get(path, **kwargs)
            else:
                r = self.get(next_link,
                             **{'headers': kwargs.get('headers', {})})
            items.extend(r['items'])
            if 'nextLink' not in r:
                break
            next_link = r['nextLink']
        return items

    def get_workbench_alerts(self, start=None, end=None):
        params = {}
        if start is not None:
            params['startDateTime'] = get_datetime_param(start)
        if end is not None:
            params['endDateTime'] = get_datetime_param(end)
        return self.get_items('/v3.0/workbench/alerts', params=params)

    def get_oat(self, start=None, end=None, top=None):
        params = {}
        if start is not None:
            params['detectedStartDateTime'] = get_datetime_param(start)
        if end is not None:
            params['detectedEndDateTime'] = get_datetime_param(end)
        if top is not None:
            params['top'] = top
        return self.get_items('/v3.0/oat/detections', params=params)

    def get_detection(self, start=None, end=None, top=None):
        params = {}
        if start is not None:
            params['startDateTime'] = get_datetime_param(start)
        if end is not None:
            params['endDateTime'] = get_datetime_param(end)
        if top is not None:
            params['top'] = top
        headers = {'TMV1-QUERY': 'hostName: *'}
        return self.get_items('/v3.0/search/detections',
                              params=params, headers=headers)

    def get_audit_logs(self, start=None, end=None, top=None):
        params = {'labels': 'all'}
        if start is not None:
            params['startDateTime'] = get_datetime_param(start)
        if end is not None:
            params['endDateTime'] = get_datetime_param(end)
        if top is not None:
            params['top'] = top
        return self.get_items('/v3.0/audit/logs', params=params)


def correct_data(docs):
    """
    This function correct VisionOne data for Elasticsearch

    1. The workbench detail has ['impactScope'][N]['entityValue'] and
       ['indicators'][N]['objectValue'] have two kinds of types; One is string
       and the other is object.
       Because Elasticsearch cannot define the union of both string and object,
       this function renames the 'entityValue' and 'objectValue' fields as the
       same as the value of 'entityType' and 'objectType' fields, respectively.

    2. The three kinds of data have different names for timestamp.
       This function names the same field for timestamp, 'esBaseDateTime'.

    3. Both workbench and detections have the 'severity' field with different
       type; Workbench is string and detections is integer.
       Because Elasticsearch cannot define the union of both string and
       integer, this function name the string field to another one,
       'severityString'.

    4. The observed techniques have the
       ['filters'][N]['highligthtedObjects'][M]['value'] with different types
       specified by ['filters'][N]['highligthedObject'][M]['type'] field;
       For example, when 'type' is 'port', 'value' is integer: when 'type' is
       'text', 'value' is string.
       Because Elasticsearch cannot define the union of all types, this
       function renames the value field as the same as the value of 'type'
       field; For example, 'type': 'host', 'host': xxx.
       In addition, some values, such as for the 'field' is 'ruleId', are not
       string type even when 'type' is 'text'. So, these values are forced to
       be stringized.

    5. The observed techniques have the ['detail']['proto'] that has two kinds
       of types; One is string and the other is integer.
       Because Elasticsearch cannot define the union of both string and
       integer, this function names the string field to another one,
       'protoString'.
    """
    for d in docs['workbench']:
        for entity in d['impactScope']['entities']:
            entity[entity['entityType']] = entity['entityValue']
            del entity['entityValue']
        for entity in d['indicators']:
            entity[entity['type']] = entity['value']
            del entity['value']
        if 'severity' in d:
            d['severityString'] = d['severity']
            del d['severity']
        d['esBaseDateTime'] = d['createdDateTime']
    for d in docs['observed_techniques']:
        d['esBaseDateTime'] = d['detectedDateTime']
        for f in d.get('filters', []):
            for obj in f.get('highlightedObjects', []):
                if (('text' == obj['type']) and
                   (not isinstance(obj['value'], str))):
                    obj['value'] = str(obj['value'])
                obj[obj['type']] = obj['value']
                del obj['value']
        if ('detail' in d) and ('proto' in d['detail']):
            if isinstance(d['detail']['proto'], str):
                d['detail']['protoString'] = d['detail']['proto']
                del d['detail']['proto']
    if 'detections' in docs:
        for d in docs['detections']:
            d['esBaseDateTime'] = d['eventTimeDT'].replace('+00:00', 'Z')
    if 'audit_logs' in docs:
        for d in docs['audit_logs']:
            d['esBaseDateTime'] = d['loggedDateTime']


def index_data_to_es(es, docs):
    def index_actions(name, data):
        for source in data:
            yield {
                '_index': name,
                '_op_type': 'index',
                '_source': source
            }
    for name, data in docs.items():
        elasticsearch.helpers.bulk(es, index_actions(name, data))


def pull_v1_data_to_es(v1, es, start, end, index_prefix, include_detections,
                       include_audit_logs):
    if not es.ping():
        raise RuntimeError('Elasticsearch server unavailable')
    docs = {}
    docs['workbench'] = v1.get_workbench_alerts(start, end)
    print(f'Retrieved workbench alerts: {len(docs["workbench"])}')
    docs['observed_techniques'] = v1.get_oat(start, end,
                                             TmV1Client.oat_top[-1])
    print('Retrieved Observed Attack Techniques events: '
          f'{len(docs["observed_techniques"])}')
    if include_detections:
        docs['detections'] = v1.get_detection(start, end,
                                              TmV1Client.search_top[-1])
        print(f'Retrieved detections: {len(docs["detections"])}')
    if include_audit_logs:
        docs['audit_logs'] = v1.get_audit_logs(start, end,
                                               TmV1Client.audit_logs_top[-1])
        print(f'Retrieved audit logs: {len(docs["audit_logs"])}')

    correct_data(docs)
    for name in list(docs.keys()):
        docs[index_prefix + name] = docs[name]
        del docs[name]
    index_data_to_es(es, docs)


def main(start, end, days, v1_token, v1_url, detections, audit_logs, es_url,
         prefix, es_user, es_password, es_cafile, es_capath, es_certfile,
         es_keyfile):
    if end is None:
        end = datetime.datetime.now(datetime.timezone.utc)
    else:
        end = datetime.datetime.fromisoformat(end)
    if start is None:
        start = end + datetime.timedelta(days=-days)
    else:
        start = datetime.datetime.fromisoformat(start)
    host = [es_url]
    basic_auth = None
    ssl_context = None
    if es_user:
        if not es_password:
            es_password = getpass.getpass()
        basic_auth = (es_user, es_password)
    if 'https' == urllib.parse.urlparse(es_url).scheme:
        ssl_context = ssl.create_default_context(
            cafile=es_cafile,
            capath=es_capath
        )
    if ssl_context and (es_certfile or es_keyfile):
        ssl_context.load_cert_chain(
            certfile=es_certfile,
            keyfile=es_keyfile
        )
    v1 = TmV1Client(v1_token, v1_url)
    es = elasticsearch.Elasticsearch(
        host,
        basic_auth=basic_auth,
        ssl_context=ssl_context
    )
    pull_v1_data_to_es(v1, es, start, end, prefix, detections, audit_logs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Send Workbench alerts, other detection data and audit'
                     ' logs to Elasticsearch'),
        epilog=(f'Example: python {os.path.basename(__file__)} '
                '-e 2021-04-12T14:28:00.123456+00:00 -d 5 -D'))
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help='Authentication token of your Trend Vision One user account')
    parser.add_argument(
        '-u', '--v1-url',
        default=TmV1Client.base_url_default,
        help=('URL of the Trend Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
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
        '-D', '--detections', action='store_true',
        help=('Parameter that searches the "Detections" data via API'
              ' and sends matching records to Elasticsearch'))
    parser.add_argument(
        '-a', '--audit-logs', action='store_true',
        help=('Parameter that searches audit logs data using the API'
              ' and sends matching records to Elasticsearch.'))
    parser.add_argument(
        '-E', '--es-url', default=ES_URL,
        help=('URL of the Elasticsearch server. The default value is'
              f' "{ES_URL}"'))
    parser.add_argument(
        '-p', '--prefix', default=ES_INDEX_PREFIX,
        help=('Prefix of indices in Elasticsearch. The default value is'
              f' "{ES_INDEX_PREFIX}"'))
    parser.add_argument(
        '-U', '--es-user', default=ES_USER,
        help='Username for Elasticsearch authentication')
    parser.add_argument(
        '-P', '--es-password', default=ES_PASSWORD,
        help=('Password for Elasticsearch authentication. If you specify'
              ' the username parameter ("--es-user") but not the password'
              ' parameter (--es-password), the system prompts you for'
              ' the password.'))
    parser.add_argument(
        '-f', '--es-cafile', default=ES_CAFILE,
        help=('Path to a file containing a CA certificate for TLS or SSL'
              ' connection to Elasticsearch'))
    parser.add_argument(
        '-c', '--es-capath', default=ES_CAPATH,
        help=('Path to a directory containing CA certificates for TLS or SSL'
              ' connection to Elasticsearch'))
    parser.add_argument(
        '-C', '--es-certfile', default=ES_CERTFILE,
        help=('Path to a file containing a certificate for TLS or SSL'
              ' connection to Elasticsearch'))
    parser.add_argument(
        '-k', '--es-keyfile', default=ES_KEYFILE,
        help=('Path to a file containing a private key for TLS or SSL'
              ' connection to Elasticsearch'))
    main(**vars(parser.parse_args()))
