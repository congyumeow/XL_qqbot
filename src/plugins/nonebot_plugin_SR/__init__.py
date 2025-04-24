import os
import re

from nonebot import on_command
from nonebot.adapters.qq import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

from .data_source import check_info, insert_user_info, query_user_info, get_data, buquan_gachaLogss, updata_user_info
from .render import draw

__plugin_meta__ = PluginMetadata(
    name="崩铁抽卡分析",
    description="崩铁抽卡记录分析",
    usage="使用指令\"/崩铁抽卡记录帮助\"查看帮助",
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.1.0"
    }
)

srgacha_bind = on_command("绑定崩铁角色", priority=5, block=True)
srgacha_gachalogs = on_command("崩铁抽卡记录", priority=5, block=True)
srgacha_gachalogs_add = on_command("补充崩铁抽卡记录", priority=5, block=True)
srgacha_help = on_command("崩铁抽卡记录帮助", priority=5, block=True)

@srgacha_bind.handle()
async def _(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().split(" ")
    qq = event.get_user_id()
    uid = arg[0]
    authkey = re.findall(r"authkey=(.*?)&game", arg[1])[0]
    if check_info(arg[1]):
        user_info = query_user_info(qq)
        if user_info is None:
            insert_user_info(qq, uid, authkey)
            await srgacha_bind.finish("绑定成功，使用指令\"崩铁抽卡记录\"查看抽卡记录分析")
        else:
            state["authkey"] = authkey
    else:
        await srgacha_bind.finish("绑定失败,用户信息查询失败，请验证后重新绑定")


@srgacha_bind.got("if_cover", prompt="已设置过抽卡信息，输入\"是\"覆盖已有信息，输入其他内容取消")
async def _(state: T_State, event: Event):
    qq = event.get_user_id()
    answer = state["if_cover"].extract_plain_text().strip()
    if answer == "是":
        updata_user_info(qq, authkey=state["authkey"])
        await srgacha_bind.finish("覆盖成功，使用指令\"崩铁抽卡记录\"查看抽卡记录分析")
    else:
        await srgacha_bind.finish("取消绑定")


@srgacha_gachalogs.handle()
async def _(bot: Bot, event: Event):
    qq = event.get_user_id()
    user_info = query_user_info(qq)
    if user_info is None:
        await srgacha_gachalogs.finish("请先绑定抽卡信息，使用指令\"绑定崩铁角色\"绑定")

    data = get_data(qq)
    img = draw(data["data"])
    msg = MessageSegment.file_image(img)
    os.remove(img)
    await srgacha_gachalogs.finish(msg)


@srgacha_gachalogs_add.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    qq = event.get_user_id()
    user_info = query_user_info(qq)
    if user_info is None:
        await srgacha_gachalogs_add.finish("请先绑定抽卡信息，使用指令\"绑定崩铁角色\"绑定")
    args = args.extract_plain_text().strip().split(" ")
    message = """
                正确指令为：/补充崩铁抽卡记录 参数1 参数2 参数3 参数4
                参数1：修改/添加
                参数2：角色池/光锥池/常驻池/新手池
                参数3：角色名(例：彦卿)
                参数4：抽取所用次数(例：75)
            """
    if args[0] not in ["修改", "添加"]:
        await srgacha_gachalogs_add.finish(message)
    if args[1] not in ["角色池", "光锥池", "常驻池", "新手池"]:
        await srgacha_gachalogs_add.finish(message)
    data = buquan_gachaLogss(qq, args)
    img = draw(data)
    msg = MessageSegment.file_image(img)
    os.remove(img)
    await srgacha_gachalogs_add.finish(msg)

@srgacha_help.handle()
async def _(bot: Bot, event: Event):
    msg = """
        发送 "鸣潮抽卡信息绑定 player_id 抽卡链接" 即可绑定抽卡信息，可长期使用
        例如 鸣潮抽卡信息绑定 101010101 https://public-operation-hkrpg.mihoyo.com……
    """
