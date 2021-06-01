import json
import os
import argparse
import datetime

import requests

# default settings
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')


def check_datetime_aware(d):
    return (d.tzinfo is not None) and (d.tzinfo.utcoffset(d) is not None)


class TmV1Client:
    base_url_default = V1_URL
    WB_STATUS_NEW = 0
    WB_STATUS_IN_PROGRESS = 1

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

    def put(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.put(self.base_url + path, **kwargs)
        if ((200 == r.status_code)
                and ('application/json' in r.headers.get('Content-Type', ''))):
            return r.json()
        raise RuntimeError(f'Request unsuccessful (PUT {path}):'
                           f' {r.status_code} {r.text}')

    def list_workbench(self, start, end, status_list=None,
                       offset=None, size=None):
        if not check_datetime_aware(start):
            start = start.astimezone()
        if not check_datetime_aware(end):
            end = end.astimezone()
        start = start.astimezone(datetime.timezone.utc)
        end = end.astimezone(datetime.timezone.utc)
        start = start.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        end = end.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        # API returns data in the range of [offset, offset+limit)
        return self.post('/v2.0/xdr/workbench/workbenches/history', json=dict([
            ('startTime', start), ('endTime', end), ('sortBy', '-createdTime')
        ]
            + ([('investigationStatus', status_list)]
                if status_list is not None else [])
            + ([('offset', offset)] if offset is not None else [])
            + ([('limit', size)] if size is not None else [])
        ))['data']['workbenchRecords']

    def get_workbench(self, workbench_id):
        return self.get(
            f'/v2.0/xdr/workbench/workbenches/{workbench_id}'
        )['data']

    def update_workbench(self, workbench_id, status):
        return self.put(
            f'/v2.0/xdr/workbench/workbenches/{workbench_id}',
            json={'investigationStatus': status})

    def query_endpoint_info(self, computer_id):
        return self.post('/v2.0/xdr/eiqs/query/endpointInfo', json={
            'computerId': computer_id
        })['result']

    def isolate_endpoint(self, computer_id):
        return self.post('/v2.0/xdr/response/isolate', json={
            'computerId': computer_id})

    def add_workbench_notes(self, workbench_id, notes):
        return self.post(
            f'/v2.0/xdr/workbench/workbenches/{workbench_id}/notes',
            json={'content': notes})

    def search_message_activities(self, start, end, query):
        return self.post('/v2.0/xdr/search/data', json={
            'fields': [],
            'from': int(start.timestamp()),
            'to': int(end.timestamp()),
            'source': 'messageActivityData',
            'query': query})

    def quarantine_message(self, mail_message_id, mailbox,
                           mail_message_delivery_time):
        return self.post('/v2.0/xdr/response/quarantineMessage', json={
            'messageId': mail_message_id, 'mailBox': mailbox,
            'messageDeliveryTime': mail_message_delivery_time,
            'description': 'A message quarantined by API'})


def fetch_new_workbench_alerts(v1, start, end):
    """
    This function do the loop to get all workbench alerts by changing
    the parameters of both 'offset' and 'size'.
    """
    offset = 0
    size = 100
    alerts = []
    while True:
        gotten = v1.list_workbench(
            start, end, [TmV1Client.WB_STATUS_NEW], offset, size)
        if not gotten:
            break
        print(f'New Workbench alerts ({offset} {offset+size}): {len(gotten)}')
        alerts.extend(gotten)
        offset = len(alerts)
    return alerts


def create_message_query(message_entity, indicators):
    query = f"recipient:{entity['entityValue']}"
    for indicator in indicators:
        if (indicator['id'] in entity['relatedIndicators']
                and indicator['objectType'] == 'url'):
            query += (f" AND url:{indicator['objectValue']}")
    return query


def main(start, end, days, v1_token, v1_url):
    if end is None:
        end = datetime.datetime.now(datetime.timezone.utc)
    else:
        end = datetime.datetime.fromisoformat(end)
    if start is None:
        start = end + datetime.timedelta(days=-days)
    else:
        start = datetime.datetime.fromisoformat(start)
    v1 = TmV1Client(v1_token, v1_url)

    wb_records = fetch_new_workbench_alerts(v1, start, end)
    if not wb_records:
        print('No Workbench alerts found')
        return
    print('')
    print('Target Workbench alerts:')
    print(json.dumps([x['workbenchId'] for x in wb_records], indent=2))
    print('')

    isolated_endpoints = []
    quarantined_messages = []
    for record in wb_records:
        wb_id = record['workbenchId']
        v1.update_workbench(wb_id, TmV1Client.WB_STATUS_IN_PROGRESS)
        workbench = v1.get_workbench(wb_id)
        impact_scope = workbench['impactScope']
        for entity in impact_scope:
            entity_type = entity['entityType']
            if entity_type == 'host':
                accounts = entity['relatedEntities']
                computer_id = entity['entityValue']['guid']
                endpoint_info = v1.query_endpoint_info(computer_id)
                if not endpoint_info:
                    continue
                if endpoint_info['productCode'] == 'sao':
                    msg = (
                        f"Endpoint {endpoint_info['ip']['value']} isolated. "
                        f'Please check it.{os.linesep}'
                        f'Related acounts = {accounts}')
                    v1.isolate_endpoint(computer_id)
                    v1.add_workbench_notes(wb_id, msg)
                    isolated_endpoints.append(endpoint_info['ip']['value'])
                else:
                    msg = ('Nothing has done with this endpoint '
                           f"{endpoint_info['ip']['value']}. Please check it."
                           f'{os.linesep}Related acounts = {accounts}')
                    v1.add_workbench_notes(wb_id, msg)
            elif entity_type == 'emailAddress':
                query = create_message_query(entity, workbench['indicators'])
                mail_logs = v1.search_message_activities(
                    start, end, query)['data']['logs']
                if mail_logs:
                    for mail in mail_logs:
                        msg = ('A message quarantined.'
                               f"Subject = {mail['mail_message_subject']}"
                               ' Please check it.')
                        v1.quarantine_message(**mail)
                        v1.add_workbench_notes(wb_id, msg)
                        quarantined_messages.append(
                            mail['mail_message_subject'])
            print('\rAffected entities that received response actions: '
                  f'{len(isolated_endpoints) + len(quarantined_messages)}',
                  end='')
    print('')
    if isolated_endpoints:
        print('')
        print('IP addresses of isolated endpoints:')
        print(json.dumps(isolated_endpoints, indent=2))
    if quarantined_messages:
        print('')
        print('Subject lines of quarantined email messages:')
        print(json.dumps(quarantined_messages, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Take a response action on the highlighted object '
                     'in a Workbench alert'),
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
        help=('Authentication token of your Trend Micro Vision One'
              ' user account'))
    parser.add_argument(
        '-r', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Micro Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    main(**vars(parser.parse_args()))
