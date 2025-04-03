import os

from nonebot import on_command
from nonebot.adapters.qq import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

from .data_source import check_info, insert_user_info, query_user_info, get_data, buquan_gachaLogss
from .render import draw

__plugin_meta__ = PluginMetadata(
    name="鸣潮抽卡分析",
    description="鸣潮抽卡记录分析",
    usage="试用指令\"/抽卡记录帮助\"查看帮助",
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.0.0"
    }
)

wwgacha_bind = on_command("绑定鸣潮角色", priority=5, block=True)
wwgacha_gachalogs = on_command("抽卡记录", priority=5, block=True)
wwgacha_gachalogs_add = on_command("补充抽卡记录", priority=5, block=True)
wwgacha_help = on_command("抽卡记录帮助", priority=5, block=True)


@wwgacha_bind.handle()
async def _(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().split(" ")
    qq = event.get_user_id()
    uid = arg[0]
    record_id = arg[1]
    if check_info(uid, record_id):
        user_info = query_user_info(qq)
        if user_info is None:
            insert_user_info(qq, uid, record_id)
            await wwgacha_bind.finish("绑定成功，使用指令\"抽卡记录\"查看抽卡记录分析")
        else:
            state["if_cover"] = "是"
            state["user_info"] = user_info
    else:
        await wwgacha_bind.finish("绑定失败,用户信息查询失败，请验证后重新绑定")


@wwgacha_bind.got("if_cover", prompt="已设置过抽卡信息，输入\"是\"覆盖已有信息，输入其他内容取消")
async def _(state: T_State, event: Event):
    qq = event.get_user_id()
    if state["if_cover"] == "是":
        user_info = state["user_info"]
        insert_user_info(qq, user_info["uid"], user_info["record_id"])
        await wwgacha_bind.finish("覆盖成功，使用指令\"抽卡记录\"查看抽卡记录分析")
    else:
        await wwgacha_bind.finish("取消绑定")


@wwgacha_gachalogs.handle()
async def _(bot: Bot, event: Event):
    qq = event.get_user_id()
    user_info = query_user_info(qq)
    if user_info is None:
        await wwgacha_gachalogs.finish("请先绑定抽卡信息，使用指令\"绑定鸣潮角色\"绑定")

    data = get_data(qq)
    img = draw(data["data"])
    msg = MessageSegment.file_image(img)
    os.remove(img)
    await wwgacha_gachalogs.finish(msg)


@wwgacha_gachalogs_add.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    qq = event.get_user_id()
    user_info = query_user_info(qq)
    if user_info is None:
        await wwgacha_gachalogs_add.finish("请先绑定抽卡信息，使用指令\"绑定鸣潮角色\"绑定")
    args = args.extract_plain_text().strip().split(" ")
    message = """
                正确指令为：/补充抽卡记录 参数1 参数2 参数3 参数4
                参数1：修改/添加
                参数2：角色池/武器池/常驻角色池/常驻武器池/新手池/新手自选池/感恩角色
                参数3：角色名(例：卡卡罗)
                参数4：抽取所用次数(例：75)
            """
    if args[0] not in ["修改", "添加"]:
        await wwgacha_gachalogs_add.finish(message)
    if args[1] not in ["角色池", "武器池", "常驻角色池", "常驻武器池", "新手池", "新手自选池", "感恩唤取"]:
        await wwgacha_gachalogs_add.finish(message)
    data = buquan_gachaLogss(qq, args)
    img = draw(data)
    msg = MessageSegment.file_image(img)
    os.remove(img)
    await wwgacha_gachalogs_add.finish(msg)


@wwgacha_help.handle()
async def _(bot: Bot, event: Event):
    help_msg = """
        PC端方法
        1.进入游戏，打开唤取界面，点击唤取记录
        2.右键鸣潮图标，选择打开文件所在位置
        3.依次打开目录 Wuthering Waves Game\\Client\\Saved Logs 找到 Client.log 文件
        4.使用文本编辑器打开，ctrl + F搜索 https://aki-gm-resources.aki-game.com/aki/gacha/index.html 找到位置
        5.找到链接携带的player_id和record_id参数
        6.发送 "鸣潮抽卡信息绑定 player_id record_id" 即可绑定抽卡信息，可长期使用
        例如：绑定鸣潮角色 100123456 b3545192e2d8ac6a6b0d069e6f54e83f
    """
    await wwgacha_help.finish(help_msg)

