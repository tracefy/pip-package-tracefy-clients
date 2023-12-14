import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


class SlackClient:

    def __init__(self):
        self.token = os.getenv("SLACK_TOKEN", "")

    def send(self, text, channel, blocks=None):
        try:
            requests.post('https://slack.com/api/chat.postMessage', {
                'token': self.token,
                'channel': channel,
                'text': text,
                'blocks': json.dumps(blocks) if blocks else None
            }).json()
        except Exception as e:
            print(e)
