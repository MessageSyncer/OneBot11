from model import *
from util import *
import image


@dataclass
class OneBot11Config(PusherConfig):
    pass


@dataclass
class Contacter:
    id: str = ''
    private: bool = False


@dataclass
class OneBot11InstanceConfig(PusherInstanceConfig):
    image_send_method: str = 'url'  # [url, base64, file]
    url: str = ''
    token: str = None  # None means auth is not needed
    contact: dict[str, Contacter] = field(default_factory=lambda: {})


class OneBot11(Pusher[OneBot11Config, OneBot11InstanceConfig]):
    async def push(self, content: Struct, to: str):
        message_field = []

        for i, element in enumerate(content.content):
            type_ = type(element)
            if type_ == StructText:
                message_field.append(
                    {
                        "type": "text",
                        "data": {
                            "text": element.text
                        }
                    }
                )
            elif type_ == StructImage:
                imageurl = ''
                image_send_method = self.instance_config.get('image_send_method', 'url')
                if image_send_method == 'base64':
                    imageurl = 'base64://' + image.image_to_base64(element.source)
                elif image_send_method == 'url':
                    imageurl = element.source
                elif image_send_method == 'file':
                    imageurl = 'file:///' + element.source
                message_field.append(
                    {
                        "type": "image",
                        "data": {
                            "file": imageurl
                        }
                    }
                )

        to = self.instance_config['contact'][to]
        private = to['private']
        url = self.instance_config['url']

        if private:
            json_ = {
                "user_id": int(to['id']),
                "message": message_field
            }
            url = url + '/send_private_msg'
        else:
            json_ = {
                "group_id": int(to['id']),
                "message": message_field
            }
            url = url + '/send_group_msg'
        headers = {
            'Content-Type': 'application/json'
        }
        if token := self.instance_config.get('token', None):
            headers['Authorization'] = f'Bearer {token}'

        response = requests.post(url, json=json_, headers=headers)

        if not response.ok:
            raise Exception(response.text)

        response = response.json()
        if response.get('status') == 'failed':
            raise Exception(response.get('message', response))
