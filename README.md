# mm-list-channels

Get mattermost public channel list.  
Post channel list.

https://mattermost.com/  
https://api.mattermost.com/

Use [AWS SAM](https://docs.aws.amazon.com/serverless-application-model/index.html).

### setup

template.yaml

- MM_BASE_URL
- MM_TEAM_ID
- MM_POST_CHANNEL_ID
- MM_TOKEN

### build

```bash
sam build --use-container
```

### local invoke

- EventBridge Channel list

```bash
sam local invoke MmListChannelsFunction -e events/event.json
```

- API Gateway Channel list

```bash
sam local invoke MmListChannelsApiFunction -e events/api_event.json
```

### deploy

```bash
sam deploy --guided [--profile xxxx]
```
