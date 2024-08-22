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
    max_image_count: int = 15


class OneBot11(Pusher[OneBot11Config, OneBot11InstanceConfig]):
    async def push(self, content: Struct, to: str):
        message_field = []

        images = [element for element in content.content if type(element) == StructImage]
        for i, image_ in enumerate(images):
            if i+1 > self.instance_config.max_image_count:
                if i+1 == self.instance_config.max_image_count+1:
                    index = content.content.index(image_)
                    content.content[index] = StructText(f'（等{len(images)}张图片）\n')
                else:
                    content.content.remove(image_)

        for i, element in enumerate(content.content):
            type_ = type(element)
            if type_ == StructText:
                if len(message_field) != 0:
                    if message_field[-1]['type'] == 'image':  # 手机端QQ会吃掉紧随图片后的文本块的一个换行，所以多加一个换行给它吃
                        message_field.append(
                            {
                                "type": "text",
                                "data": {
                                    "text": '\n'
                                }
                            }
                        )
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
