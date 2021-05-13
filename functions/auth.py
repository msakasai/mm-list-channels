import os


def lambda_handler(event, context):
    """ Lambda Authorizer """
    print(event)
    
    tmp = event['methodArn'].split(':')
    api_gateway_arn_tmp = tmp[5].split('/')

    region = tmp[3]
    account_id = tmp[4]
    api_id = api_gateway_arn_tmp[0]
    stage = api_gateway_arn_tmp[1]

    token = event["authorizationToken"]
    # print(token)
    
    effect = "Allow" if token == f"Token {os.getenv('MM_SLACH_CMD_TOKEN')}" else "Deny"

    res = {
        "principalId" : 1,
        "policyDocument" : {
            "Version" : "2012-10-17",
            "Statement" : [
                {
                    "Action": "*",
                    "Effect": effect,
                    "Resource": f"arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/*/*"
                }
            ]
        }
    }
    print(res)

    return res
