import os
import json
import requests
from jinja2 import Template
from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

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
    """ EventBridge Handler """
    event: EventBridgeEvent = EventBridgeEvent(event)
    mm_list_channels()

    return 0

@middleware_before_after
def api_handler(event, context):
    """ API Gateway Handler """
    # print(event)
    event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
    mm_list_channels(event['queryStringParameters'])

    return {
        'statusCode': 200,
        'body': '{"message": "Channel list OK."}'
    }


def mm_list_channels(params: dict = {}):
    # print(params)
    mm_channels = MmChannels(
        os.getenv('MM_TOKEN'),
        os.getenv('MM_BASE_URL'),
        os.getenv('MM_TEAM_ID') if not params else params['team_id'],
        os.getenv('MM_POST_CHANNEL_ID') if not params else params['channel_id'],
        None if not params else params['user_id'],
        False if not params else True
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
        'token',
        'base_url',
        'team_id',
        'post_channel_id',
        'user_id',
        'ephemeral',
        'mm_channels_api_url',
        'mm_post_api_url',
        'channels'
    ]

    def __str__(self):
        return f'Public channel list post. base_url: {self.base_url}, team_id: {self.team_id}, post_channel_id: {self.post_channel_id}, user_id: {self.user_id}, mm_channels_api_url: {self.mm_channels_api_url}, mm_post_api_url: {self.mm_post_api_url}'

    def __init__(self, _token: str, _base_url: str, _team_id: str, _post_channel_id: str, _user_id: str, _ephemeral: bool):
        self.token = _token
        self.base_url = _base_url
        self.team_id = _team_id
        self.post_channel_id = _post_channel_id
        self.user_id = _user_id
        self.ephemeral = _ephemeral
        self.mm_channels_api_url = f'{_base_url}/api/v4/teams/{self.team_id}/channels'
        self.mm_post_api_url = f'{_base_url}/api/v4/posts' + ('/ephemeral' if self.ephemeral else '')

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

        _params = {
            'channel_id': self.post_channel_id,
            'message': _post_text,
        }
        if self.ephemeral:
            params = {
                'user_id': self.user_id,
                'post': _params
            }
        else:
            params = _params
        # print(params)

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
