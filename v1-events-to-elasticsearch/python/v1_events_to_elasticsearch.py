import datetime
import argparse
import os
import urllib.parse
import ssl
import getpass

import requests
import elasticsearch
import elasticsearch.helpers

# default settings
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
ES_URL = os.environ.get('TMV1_ELASTICSEARCH_URL', 'http://localhost:9200')
ES_INDEX_PREFIX = os.environ.get('TMV1_ELASTICSEARCH_INDEX_PREFIX', 'tmv1_')
ES_USER = os.environ.get('TMV1_ELASTICSEARCH_USER')
ES_PASSWORD = os.environ.get('TMV1_ELASTICSEARCH_PASSWORD')
ES_CAFILE = os.environ.get('TMV1_ELASTICSEARCH_CAFILE')
ES_CAPATH = os.environ.get('TMV1_ELASTICSEARCH_CAPATH')
ES_CERTFILE = os.environ.get('TMV1_ELASTICSEARCH_CERTFILE')
ES_KEYFILE = os.environ.get('TMV1_ELASTICSEARCH_KEYFILE')


def check_datetime_aware(d):
    return (d.tzinfo is not None) and (d.tzinfo.utcoffset(d) is not None)


class TmV1Client:
    base_url_default = V1_URL
    oat_size_default = 50
    # API seems to have the maximum value of 'size' parameter, 200
    oat_size_max = 200

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

    def get(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.get(self.base_url + path, **kwargs)
        if ((200 == r.status_code)
                and ('application/json' in r.headers.get('Content-Type', ''))):
            return r.json()
        raise RuntimeError(f'Request unsuccessful (GET {path}):'
                           f' {r.status_code} {r.text}')

    def post(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.post(self.base_url + path, **kwargs)
        if ((200 == r.status_code)
                and ('application/json' in r.headers.get('Content-Type', ''))):
            return r.json()
        raise RuntimeError(f'Request unsuccessful (POST {path}):'
                           f' {r.status_code} {r.text}')

    def get_workbench_histories(self, start, end, offset=None, size=None):
        if not check_datetime_aware(start):
            start = start.astimezone()
        if not check_datetime_aware(end):
            end = end.astimezone()
        start = start.astimezone(datetime.timezone.utc)
        end = end.astimezone(datetime.timezone.utc)
        start = start.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        end = end.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        # API returns data in the range of [offset, offset+limit)
        return self.get(
            '/v2.0/xdr/workbench/workbenchHistories',
            params=dict([('startTime', start), ('endTime', end),
                        ('sortBy', '-createdTime')]
                        + ([('offset', offset)] if offset is not None else [])
                        + ([('limit', size)] if size is not None else [])
                        ))['data']['workbenchRecords']

    def get_oat(self, start, end, size=None, nextBatchToken=None):
        if size is None:
            size = TmV1Client.oat_size_default
        start = int(start.timestamp())
        end = int(end.timestamp())
        # API returns data in the range of [start, end]
        data = self.get('/v2.0/xdr/oat/detections', params=dict([
            ('start', start), ('end', end), ('size', size),
        ]
            + ([('nextBatchToken', nextBatchToken)]
                if nextBatchToken is not None else [])
        ))['data']
        return data['detections'], data.get('nextBatchToken', '')

    def get_detection(self, start, end, offset=None, query=None):
        return self.post('/v2.0/xdr/search/data', json=dict([
            ('fields', []),
            ('from', int(start.timestamp())),
            ('to', int(end.timestamp())),
            ('source', 'detections'),
            ('query', query if query is not None else 'hostName: *')
        ]
            + ([('offset', offset)] if offset is not None else [])
        ))['data']['logs']


def fetch_workbench_alerts(v1, start, end):
    """
    This function do the loop to get all workbench alerts by changing
    the parameters of both 'offset' and 'size'.
    """
    offset = 0
    size = 100
    alerts = []
    while True:
        gotten = v1.get_workbench_histories(start, end, offset, size)
        if not gotten:
            break
        print(f'Workbench alerts ({offset} {offset+size}): {len(gotten)}')
        alerts.extend(gotten)
        offset = len(alerts)
    return alerts


def fetch_observed_attack_techniques(v1, start, end):
    """
    This functions do the loop to get the oat events by changing the parameters
    of 'nextBatchToken' if the response has it.
    """
    if not check_datetime_aware(start):
        start = start.astimezone()
    if not check_datetime_aware(end):
        end = end.astimezone()
    start = start.astimezone(datetime.timezone.utc)
    end = end.astimezone(datetime.timezone.utc)
    detections = []
    size = TmV1Client.oat_size_max
    next_token = ''
    offset = 0
    while True:
        gotten, next_token = v1.get_oat(start, end, size, next_token)
        print(f'Observed Attack Technique events({offset} {offset+size}):'
              f' {len(gotten)}')
        detections.extend(gotten)
        if not next_token:
            break
        offset = len(detections)
    return detections


def fetch_detections(v1, start, end):
    """
    This function do the loop to get the detections by changing the parameter
    of the offset.
    """
    offset = 0
    logs = []
    while True:
        gotten = v1.get_detection(start, end, offset)
        if not gotten:
            break
        print(f'Other detections({start} {end}): {len(gotten)}')
        logs.extend(gotten)
        offset = len(logs)
    return logs


def correct_data(docs):
    """
    This function correct VisionOne data for Elasticsearch

    1. The workbench detail has ['inpactScope'][N]['entityValue'] and
       ['indicators'][N]['objectValue'] have two kinds of types; One is string
       and the other is object.
       Because Elasticsearch cannot define the union of both string and object,
       this function renames the 'entityValue' and 'objectValue' fields as the
       same as the value of 'entityType' and 'objectType' fields, respectively.

    2. The three kinds of data have different names for timestamp.
       This function names the same field for timestamp, 'es_basetime'.

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
    """
    for d in docs['workbench']:
        for entity in d['detail']['impactScope']:
            entity[entity['entityType']] = entity['entityValue']
            del entity['entityValue']
        for entity in d['detail']['indicators']:
            entity[entity['objectType']] = entity['objectValue']
            del entity['objectValue']
        if 'severity' in d:
            d['severityString'] = d['severity']
            del d['severity']
        d['es_basetime'] = d['detail']['workbenchCompleteTimestamp']
    for d in docs['observed_techniques']:
        d['es_basetime'] = d['detectionTime']
        for f in d.get('filters', []):
            for obj in f.get('highlightedObjects', []):
                if (('text' == obj['type']) and
                   (not isinstance(obj['value'], str))):
                    obj['value'] = str(obj['value'])
                obj[obj['type']] = obj['value']
                del obj['value']
    if 'detections' in docs:
        for d in docs['detections']:
            d['es_basetime'] = d['eventTimeDT'].replace('+00:00', 'Z')


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


def pull_v1_data_to_es(v1, es, start, end, index_prefix, include_detections):
    if not es.ping():
        raise RuntimeError('Elasticsearch server unavailable')
    docs = {}
    docs['workbench'] = fetch_workbench_alerts(v1, start, end)
    docs['observed_techniques'] = fetch_observed_attack_techniques(
        v1, start, end)
    if include_detections:
        docs['detections'] = fetch_detections(v1, start, end)
    correct_data(docs)
    for name in list(docs.keys()):
        docs[index_prefix + name] = docs[name]
        del docs[name]
    index_data_to_es(es, docs)


def main(start, end, days, v1_token, v1_url, detections, es_url, prefix,
         es_user, es_password, es_cafile, es_capath, es_certfile, es_keyfile):
    if end is None:
        end = datetime.datetime.now(datetime.timezone.utc)
    else:
        end = datetime.datetime.fromisoformat(end)
    if start is None:
        start = end + datetime.timedelta(days=-days)
    else:
        start = datetime.datetime.fromisoformat(start)
    host = [es_url]
    http_auth = None
    ssl_context = None
    if es_user:
        if not es_password:
            es_password = getpass.getpass()
        http_auth = (es_user, es_password)
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
        http_auth=http_auth,
        ssl_context=ssl_context
    )
    pull_v1_data_to_es(v1, es, start, end, prefix, detections)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Send Workbench alerts and other detection data '
                     'to Elasticsearch'),
        epilog=(f'Example: python {os.path.basename(__file__)} '
                '-e 2021-04-12T14:28:00.123456+00:00 -d 5 -D'))
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
        '-r', '--v1-url',
        default=TmV1Client.base_url_default,
        help=('URL of the Trend Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    parser.add_argument(
        '-D', '--detections', action='store_true',
        help=('Parameter that searches the "Detections" data via API'
              ' and sends matching records to Elasticsearch'))
    parser.add_argument(
        '-E', '--es-url', default=ES_URL,
        help=('URL of the Elasticsearch server. The default value is'
              f' "{ES_URL}"'))
    parser.add_argument(
        '-p', '--prefix', default=ES_INDEX_PREFIX,
        help=('Prefix of indices in Elasticsearch. The default value is'
              f' "{ES_INDEX_PREFIX}"'))
    parser.add_argument(
        '-u', '--es-user', default=ES_USER,
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
