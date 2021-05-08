import os
import json
import requests
from jinja2 import Template
from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent

logger = Logger()


@lambda_handler_decorator
def middleware_before_after(handler, event, context):
    try:
        # logic_before_handler_execution()
        response = handler(event, context)
        # logic_after_handler_execution()
        return response
    except Exception as e:
        logger.error(e)
        raise e


@middleware_before_after
def lambda_handler(event, context):
    event: EventBridgeEvent = EventBridgeEvent(event)
    mm_list_channels(event.detail)

    return 0


def mm_list_channels(eventDetail: dict):
    mm_channels = MmChannels(
        os.getenv('MM_BASE_URL'),
        os.getenv('MM_TEAM_ID'),
        os.getenv('MM_POST_CHANNEL_ID'),
        os.getenv('MM_TOKEN'),
    )
    logger.info(mm_channels)
    
    mm_channels()


MM_POST_TEXT_TMPL = """
| # | channel | display_name | header | purpose |
|:-:|:--|:--|:--|:--|
{%- set ns = namespace(idx = 1) -%}
{% for c in chs %}
| {{ ns.idx }} | ~{{ c['name'] }} | {{ c['display_name'] }} | {{ c['header'] }} | {{ c['purpose'] }} |
{%- set ns.idx = ns.idx + 1 -%}
{%- endfor %}
"""


class MmChannels:

    __slot__ = [
        'base_url',
        'team_id',
        'post_channel_id',
        'token',
        'mm_channels_api_url',
        'channels'
    ]

    def __str__(self):
        return f'Public channel list post. base_url: {self.base_url}, team_id: {self.team_id}, post_channel_id: {self.post_channel_id}'

    def __init__(self, _base_url: str, _team_id: str, _post_channel_id: str, _token: str):
        self.base_url = _base_url
        self.team_id = _team_id
        self.post_channel_id = _post_channel_id
        self.token = _token
        self.mm_channels_api_url = f'{_base_url}/api/v4/teams/{_team_id}/channels'
        self.mm_post_api_url = f'{_base_url}/api/v4/posts'

    def channel_list(self) -> None:
        _channel_list = []

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        page = 0
        while True:
            params = {'page': page, 'per_page': 10}
            response = requests.get(self.mm_channels_api_url, headers=headers, params=params)
            
            status = response.status_code
            if status == 200:
                _channel_list += [
                    {
                        'name': d['name'], 
                        'display_name': d['display_name'], 
                        'lower_display_name': d['display_name'].lower(), 
                        'header': d['header'].replace('\n', '').replace('https://', ''),
                        'purpose': d['purpose'].replace('\n', '').replace('https://', ''),
                    } for d in response.json()]
            else:
                logger.error(response.json())
                raise Exception(status)

            if len(response.json()) < 10:
                break
            page += 1
        
        self.channels = _channel_list

    def sorted_channels(self) -> None:
        self.channels =  sorted(self.channels, key=lambda x: x['name'])

    def post_text(self) -> str:
        template = Template(MM_POST_TEXT_TMPL)
        return template.render(chs=self.channels)

    def post(self, _post_text: str) -> None:
        # print(_post_text)

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        params = {
            'channel_id': self.post_channel_id,
            'message': _post_text,
        }

        response = requests.post(self.mm_post_api_url, headers=headers, json=params)
        if (response.status_code != 201):
            logger.error(response.json())
            raise Exception(response.status_code)

    def __call__(self):
        self.channel_list()
        # print(self.channels)

        self.sorted_channels()
        # print(self.channels)
        
        self.post(self.post_text())
