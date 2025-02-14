from typing import Annotated

from nonebot import on_keyword, on_fullmatch, on_regex, require
from nonebot.adapters.qq import Bot, MessageEvent, Message, MessageSegment
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends, RegexStr
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .config import FortuneConfig, FortuneThemesDict
from .data_source import FortuneManager, fortune_manager

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # isort:skip

__fortune_version__ = "v0.4.12"
__fortune_usages__ = f"""
[今日运势/抽签/运势] 一般抽签
[xx抽签]     指定主题抽签
[指定xx签] 指定特殊角色签底，需要自己尝试哦~
[设置xx签] 设置群抽签主题
[重置主题] 重置群抽签主题
[主题列表] 查看可选的抽签主题
[查看主题] 查看群抽签主题""".strip()

__plugin_meta__ = PluginMetadata(
    name="今日运势",
    description="抽签！占卜你的今日运势🙏",
    usage=__fortune_usages__,
    type="application",
    homepage="https://github.com/MinatoAquaCrews/nonebot_plugin_fortune",
    config=FortuneConfig,
    extra={
        "author": "KafCoppelia <k740677208@gmail.com>",
        "version": __fortune_version__,
    },
)

general_divine = on_keyword({"今日运势", "抽签", "运势"}, priority=5)
change_theme = on_regex(
    r"^设置(.*?)签$",
    permission=SUPERUSER,
    priority=8,
    block=True,
)
reset_themes = on_regex(
    "^重置(抽签)?主题$",
    permission=SUPERUSER,
    priority=8,
    block=True,
)
themes_list = on_fullmatch("主题列表", priority=8, block=True)
show_themes = on_regex("^查看(抽签)?主题$", priority=8, block=True)


@show_themes.handle()
async def _(event: MessageEvent):
    gid: str = str(929148869)
    theme: str = fortune_manager.get_group_theme(gid)
    await show_themes.finish(f"当前群抽签主题：{FortuneThemesDict[theme][0]}")


@themes_list.handle()
async def _(event: MessageEvent):
    msg: str = FortuneManager.get_available_themes()
    await themes_list.finish(msg)


@general_divine.handle()
async def _(bot: Bot, event: MessageEvent):
    uid: str = str(event.get_user_id())

    is_first, image_file = fortune_manager.divine("929148869", uid, None, None)
    if image_file is None:
        await general_divine.finish("今日运势生成出错……")

    if not is_first:
        msg = "你今天抽过签了，再给你看一次哦🤗\n" + MessageSegment.file_image(image_file)
    else:
        logger.info(f"User {uid} 占卜了今日运势")
        msg = "✨今日运势✨" + MessageSegment.file_image(image_file)

    await general_divine.finish(msg)


async def get_user_arg(matcher: Matcher, args: Annotated[str, RegexStr()]) -> str:
    arg: str = args[2:-1]
    if len(arg) < 1:
        await matcher.finish("输入参数错误")

    return arg


@reset_themes.handle()
async def _(event: MessageEvent):
    gid: str = str(929148869)
    if not fortune_manager.divination_setting("random", gid):
        await reset_themes.finish("重置群抽签主题失败！")

    await reset_themes.finish("已重置当前群抽签主题为随机~")


# 清空昨日生成的图片
@scheduler.scheduled_job("cron", hour=0, minute=0, misfire_grace_time=60)
async def _():
    FortuneManager.clean_out_pics()
    logger.info("昨日运势图片已清空！")
