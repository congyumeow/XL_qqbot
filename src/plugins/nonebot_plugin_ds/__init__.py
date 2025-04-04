import nonebot
from openai import OpenAI
from nonebot import on_message
from nonebot.adapters.qq import MessageEvent
from nonebot.rule import Rule
from nonebot.plugin import PluginMetadata

from .config import base_url, api_key, setting

__plugin_meta__ = PluginMetadata(
    name="deepseek-chat",
    description="deepseek-chat",
    usage="deepseek-chat",
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.0.0"
    }
)

DEEPSEEK_API_URL = base_url
DEEPSEEK_API_KEY = api_key
SETTING = setting

COMMAND_LIST = [
    cmd for cmd in nonebot.get_driver().config.command_start
]

def get_ds_response(user_msg: str):
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)

    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": SETTING
            },
            {
                "role": "user",
                "content": user_msg
            }
        ]
    )

    return completion.choices[0].message.content


async def is_normal_messagge(event: MessageEvent) -> bool:
    text = event.get_plaintext().strip()
    return not any(
        text.startswith(cmd)
        for cmd in COMMAND_LIST
    )


ds_chat = on_message(
    priority=10,
    rule=Rule(is_normal_messagge)
)


@ds_chat.handle()
async def _(event: MessageEvent):
    user_msg = event.get_plaintext().strip()
    response = get_ds_response(user_msg)
    await ds_chat.send(response)