import re

from nonebot import on_command
from nonebot.adapters.qq import Bot, Event
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="books_qa",
    description="",
    usage="",
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.0.0"
    }
)
menu = on_command("菜单", priority=5)

groups = ["A1BA2AEAA86D1838B17CBB4B4293F008", "10AC00F9354D817EDEA7CA3F1A4EE980"]


def group_limit(group_id: str):
    if group_id not in groups:
        return False
    return True

def get_group_id(event: Event):
    descript = event.get_event_description()
    group = re.findall(r'Group:(.*?)]', descript)[0]
    return group


@menu.handle()
async def _(bot: Bot, event: Event):
    str = "命令菜单：\n1.菜单：查看命令\n2.今日运势(抽签、运势)：抽签\n3.塔罗牌：塔罗牌占卜\n4.天气：查看天气(例：天气 北京)"
    await bot.send(
        event=event,
        message=str,
        at_sender=True
    )
    # sk-dad9b732cf86456d903d311151fc4b49 # sirin_api