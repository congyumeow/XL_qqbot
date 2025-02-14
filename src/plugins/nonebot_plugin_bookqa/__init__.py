import time
import hashlib

from nonebot import on_command, on_keyword
from nonebot.adapters.qq import Bot, Event, Message, MessageEvent
from nonebot.params import Arg, CommandArg, ArgStr
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot.log import logger

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
books = on_command("作者的书", priority=5)
character = on_command('人物设定', aliases={"角色设定"}, priority=5, block=True)
followup = on_keyword({"follow","后续计划", "新书计划"}, priority=5)
rp = on_keyword({"人品", "今日人品"}, priority=5)


# welcome = on_notice()  # 加群、退群事件处理
# groups = [498271521, 929148869]  # 加群、退群处理群列表
murasame = "掌握因果法则从而突破到仙帝境界的天才少女，刚刚突破仙帝遭遇仇家业火大帝。\n" \
           "不敌对方，强行使用跨界传送术，遭遇时空乱流，肉身陨落，神魂进入丛雨丸中，之后进入时空裂缝抵达约战世界。"
ouyangxue = "星海联邦洛雨星居民欧阳雪，在一次轨道轰炸中死亡，转生成为六级文明瓦尔特文明火种歼星舰yukikaze号的舰娘。\n" \
            "在打捞星海联邦残存战舰丛雨号后，因丛雨号智能AI试图挟持yukikaze号，被yukikaze号辅助控制系统阻止后，yukikaze号辅助系统获得升级，之后yukikaze号更名为安克雷奇号。\n" \
            "第三次改造时因所需资源不足与星际流浪者妖澪姬结识，欧阳雪为其改名为东方澪，然后同行，目前位于被始皇帝统一的太阳系中。"
dongfangling = "未知文明实验中制造出来的克隆人，代号妖澪姬（107），在原文明被死神毁灭后驾驶江风号恒星级歼星舰在宇宙中流浪。\n" \
               "在北落师门的中立无人空间站中帮助欧阳雪进行星舰改造，之后被欧阳雪起名东方澪，随后与其同行，目前位于被始皇帝统一的太阳系中。"
jianglinya = "番茄免费小说作者黑色灵魂的猹《碧蓝航线：我是舰娘！》中的主角，经黑色灵魂的猹同意，在《这个舰娘有亿点冒失》中使用。\n" \
             "原形为星球大战”执行者级“超级歼星舰，舰裝组成的歼星舰：TTK-恒星级歼星舰“江林雅”号，全长26km。\n" \
             "《这个舰娘有亿点冒失》中由一块战舰核心修复而来，因受损过于严重，将欧阳雪搭建的维修池能量耗尽。\n" \
             "维修完成的江林雅因能源不足，只能在欧阳雪的援助下维持星舰的日常机能。目前位于被始皇帝统一的太阳系中，已解锁机库功能，且开放歼星舰控制权。"
qimeng = "一觉醒来发现自己变成西林小天使且来到提瓦特大陆的大学生，在偶然进入崩坏世界后融合了自己的恶念。\n" \
         "先后获得了空之律者、理之律者、时间律者、识之律者、雷之律者、炎之律者核心，在特殊特异点中融合被格犹·索托斯能量污染的终焉律者核心。"
xingling = "星泠·伊西里斯，血族第一顺位继承人，武器是血族第一始祖的遗物——死棘蔷薇。"
lvqi = "绿绮，精灵族第三位公主，武器为精灵族母树的一节树枝制作的长弓——聆音。"


@books.handle()
async def bookssend(bot: Bot, event: Event):
    autherBook = "\n对话小说：《灵之刃》《变成西琳的旅途》\n传统小说：《这个舰娘有亿点冒失》"
    await bot.send(
        event=event,
        message=autherBook,
        at_sender=True
    )


@menu.handle()
async def menusend(bot: Bot, event: Event):
    str = "命令菜单：\n1.菜单：查看命令\n2.作者的书：查看作者完结或连载中的书\n3.人物设定(角色设定)：查看书中主要任务的设定" \
          "\n4.后续计划(新书计划、follow)：查看作者后续创作计划\n5.今日运势(抽签、运势)：抽签\n6.塔罗牌：塔罗牌占卜"
    await bot.send(
        event=event,
        message=str,
        at_sender=True
    )


@character.handle()
async def charactersend(state: T_State, args: Message = CommandArg()):
    if args.extract_plain_text().strip():
        state["people"] = args.extract_plain_text().strip()


@character.got("people", prompt="请选择人物：\n1：丛雨\n2：欧阳雪\n3：东方澪\n4：江林雅\n5：绮梦\n6：星泠\n7：绿绮")
async def chose_peo(bot: Bot, event: MessageEvent,people: Message = Arg(), people_name: str = ArgStr("people")):
    if people_name not in ["丛雨", "欧阳雪", "东方澪", "江林雅", "绮梦", "星泠", "绿绮"]:
        await character.reject(people.template(f"你想查询的角色{people}暂不支持，请重新输入！"))

    if people_name == "丛雨":
        await character.finish(murasame)

    if people_name == "欧阳雪":
        await character.finish(ouyangxue)

    if people_name == "东方澪":
        await character.finish(dongfangling)

    if people_name == "江林雅":
        await character.finish(jianglinya)

    if people_name == "绮梦":
        await character.finish(qimeng)

    if people_name == "星泠":
        await character.finish(xingling)

    if people_name == "绿绮":
        await character.finish(lvqi)


@followup.handle()
async def followup_send(bot: Bot, event: Event):
    str = "作者后续准备自拟世界观，开始原创，目前已决定角色为星泠。\n星泠：血族公主，不喜欢拘束，向往星辰大海。"
    await bot.send(
        event=event,
        message=str,
        at_sender=True
    )


@rp.handle()
async def _handle(bot: Bot, event: MessageEvent):
    qq = event.get_user_id()
    t1 = time.time() // 10000
    replay = int(hashlib.md5((str(qq) + str(t1)).encode()).hexdigest(), 16) % 42 + 61
    msg = '你今天的人品值为：' + str(replay)
    logger.info(event.get_event_description())
    await rp.finish(msg, at_sender=True)