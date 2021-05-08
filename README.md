# mm-list-channels

Get mattermost public channel list.  
Post channel list.

https://mattermost.com/  
https://api.mattermost.com/


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

```bash
sam local invoke MmListChannelsFunction -e events/event.json
```

### deploy

```bash
sam deploy --guided 
```
