import math
import re

from nonebot import on_command
from nonebot.adapters.qq import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .render import *
from .config import *

__plugin_meta__ = PluginMetadata(
    name="剑与魔法RPG",
    description="文字冒险游戏插件",
    usage=(
        "指令：\n"
        "创建角色 <角色名> - 开始冒险\n"
        "状态 - 查看角色属性\n"
        "商店 - 查看商品\n"
        "合成 - 打开制作菜单\n"
        "装备 <武器名> - 更换武器\n"
        "背包 - 查看背包\n"
        "材料 - 查看材料\n"
        "战斗 - 遭遇战\n"
        "魔法阵 <设置>\<重置> - 打开魔法阵菜单\n"
        "攻击 <目标> - 攻击目标\n"
        "休息 - 恢复状态\n"
        "锻炼 - 属性成长\n"
        "探索 - 非掉落材料获取\n"
    ),
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.0.0"
    }
)

# 数据库初始化
db = OPMysql()

# 命令注册
game_menu = on_command("游戏菜单", priority=5)
create_role = on_command("创建角色", priority=5)
status = on_command("状态", priority=5)
shop = on_command("商店", priority=5)
buy = on_command("购买", priority=5)
craft = on_command("合成", priority=5)
equip = on_command("装备", priority=5)
backpack = on_command("背包", priority=5)
materials = on_command("材料", priority=5)
battle = on_command("战斗", aliases={"battle"}, priority=5)
magic = on_command("魔法阵", aliases={"magic"}, priority=5)
attack = on_command("攻击", aliases={"attack"}, priority=5)
rest = on_command("休息", priority=5)
exercise = on_command("锻炼", priority=5)
explore = on_command("探索", priority=5)


@game_menu.handle()
async def _(bot: Bot, event: Event):
    msg = """指令：
    创建角色 [角色名] - 开始冒险
    状态 - 查看角色属性
    商店 - 查看商品
    合成 - 打开制作菜单
    装备 [武器名] - 更换武器
    背包 - 查看背包
    材料 - 查看材料
    战斗 - 遭遇战
    魔法阵 [设置]\[重置] - 打开魔法阵菜单
    攻击 [目标] - 攻击目标
    休息 - 恢复状态"""
    await game_menu.finish(msg)

# --- 角色创建 ---
@create_role.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    if get_player(user_id):
        await create_role.finish("你已经创建过角色了！")

    name = args.extract_plain_text().strip()
    if not name:
        await create_role.finish("请输入角色名，例如：创建角色 亚瑟")

    # 初始化数据
    db.insertData(f"""
        INSERT INTO players (user_id, name) 
        VALUES ('{user_id}', '{name}')
        """)
    init_equipment(user_id)
    await create_role.finish(
        f"\n🎉 角色【{name}】创建成功！" +
        "\n🔧 已装备初始武器：匕首" +
        "\n📝 输入【状态】查看角色信息"
    )


# --- 状态查看 ---
@status.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    player = get_player(user_id)

    if not player:
        await status.finish("请先创建角色！")

    final = calculate_final_stats(player)

    msg = (
        f"【{player['name']}】\n"
        f"❤️ HP：{player['current_hp']}/{final['max_hp']}\n"
        f"🔵 MP：{player['current_mp']}/{final['max_mp']}\n"
        f"💪 力量：{final['ATN']} | 🧠 魔力：{final['INT']}\n"
        f"🛡️ 防御：{final['DEF']} | 👐 敏捷：{final['SPD']}\n"
        f"🗡️ 武器：{player['weapon'].get('name', '无')}\n"
        f"🛡️ 防具：{player['armor'].get('name', '无') if isinstance(player['armor'], dict) else '无'}\n"
        f"💰 金币：{player['gold']}"
    )
    await status.finish(msg)


# --- 背包查询模块 ---
@backpack.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    player = get_player(user_id)

    if not player:
        await backpack.finish("请先创建角色！")

    # 格式化背包物品
    items = []
    for item_name, quantity in player["backpack"].items():
        item_info = EQUIPMENTS.get(item_name, {}).get("name", item_name)
        items.append(f"· {item_info} ×{quantity}")

    # 添加装备信息
    current_weapon = player["weapon"].get("name", "无")

    msg = (
            "🎒 背包物品：\n" +
            ("\n".join(items) if items else "空无一物") +
            f"\n\n🗡️ 当前装备：{current_weapon}" +
            f"\n💰 持有金币：{player['gold']}"
    )

    await backpack.finish(msg)


# --- 材料查询模块 ---
@materials.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    player = get_player(user_id)

    if not player:
        await materials.finish("请先创建角色！")

    # 格式化材料列表
    materials_list = []
    for mat_name, quantity in player["material"].items():
        materials_list.append(f"· {mat_name} ×{quantity}")

    # 计算合成进度
    # craft_progress = []
    # for item, recipe in CRAFT_RECIPES.items():
    #     can_craft = True
    #     progress = []
    #     for mat, need in recipe.items():
    #         has = player["material"].get(mat, 0)
    #         progress.append(f"{mat}：{has}/{need}")
    #         if has < need:
    #             can_craft = False

        # status = "✅" if can_craft else "❌"
        # craft_progress.append(f"{status} {item}：" + " | ".join(progress))

    msg = (
            "📦 持有材料：\n" +
            ("\n".join(materials_list) if materials_list else "空空如也")
            # "\n\n🔨 可合成物品：" +
            # ("\n" + "\n".join(craft_progress) if craft_progress else "\n暂无足够材料")
    )

    await materials.finish(msg)


# --- 商店模块 ---
@shop.handle()
async def _(bot: Bot, event: Event):
    items = "\n".join([f"{name} - {info['price']}金币"
                       for name, info in ITEMS.items() if "price" in info])
    await shop.finish(
        "🛒 商店商品：\n" +
        items +
        "\n输入“购买 物品名”进行购买"
    )


@buy.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    player = get_player(user_id)
    item_name = args.extract_plain_text().strip()

    name = re.findall(r" (\S+)", event.get_plaintext())[0]
    if name.find("*") > 0:
        item_name, count = name.split("*")
        count = int(count)
    else:
        item_name = name
        count = 1

    if not item_name:
        items = "\n".join([f"{name} - {info['price']}金币"
                           for name, info in ITEMS.items() if "price" in info])
        await buy.finish(
            "🛒 商店商品：\n" +
            items +
            "\n输入“购买 物品名”进行购买"
        )

    total_price = ITEMS[item_name]["price"] * count

    if item_name not in ITEMS:
        await buy.finish("没有这个物品")
    elif player["gold"] < total_price:
        await buy.finish("金币不足，无法购买")
    else:
        player["gold"] -= total_price
        player["material"][item_name] = player["material"].get(item_name, 0) + 1

    update_player(user_id, player)

    buy.finish(f"购买成功，剩余金币：{player['gold']}")


# --- 合成模块 ---
@craft.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    player = get_player(user_id)
    item_type = args.extract_plain_text().strip().split()

    if not item_type or item_type[0] not in CRAFT_RECIPES:
        types = ', '.join(CRAFT_RECIPES.keys())
        await craft.finish(f"可合成类型：\n{types}")

    item_type, item_name = item_type if len(item_type) == 2 else (item_type, None)
    if item_name is None:
        # 显示合成列表
        recipes = "\n".join(
            f"{name}: {', '.join(f'{k}×{v}' for k, v in mats.items())}"
            for name, mats in CRAFT_RECIPES[item_type].items()
        )
        await craft.finish(f"可合成物品：\n{recipes}")

    if item_name not in CRAFT_RECIPES:
        await craft.finish("没有这个合成配方")

    # 材料检查
    required = CRAFT_RECIPES[item_type][item_name]
    missing = []
    for mat, count in required.items():
        if player["material"].get(mat, 0) < count:
            missing.append(f"{mat}×{count - player['material'].get(mat, 0)}")

    if missing:
        await craft.finish(f"材料不足，缺少：{', '.join(missing)}")

    # 执行合成
    for mat, count in required.items():
        player["material"][mat] -= count
        if player["material"][mat] == 0:
            del player["material"][mat]

    # 获得成品
    if item_name in EQUIPMENTS:
        player["backpack"][item_name] = player["backpack"].get(item_name, 0) + 1
    elif item_name in MAGIC_MATRIX:
        player["magic_circle"][item_name] = player["magic_circle"].get(item_name, 0) + 1
    update_player(user_id, player)

    await craft.finish(f"成功合成{item_name}！")


# --- 装备系统 ---
@equip.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    player = get_player(user_id)
    equip_name = args.extract_plain_text().strip()

    # 获取装备类型
    equip_type = EQUIPMENTS.get(equip_name, {}).get("type")
    if not equip_type:
        await equip.finish("未知装备")

    # 检查背包是否存在
    if equip_name not in player["backpack"]:
        await equip.finish("背包中没有该装备")

    # 根据类型处理装备
    if equip_type == "weapon":
        equip_field = "weapon"
    elif equip_type == "armor":
        equip_field = "armor"
    else:
        await equip.finish("无法装备此类型物品")

    # 应用新装备
    new_equip = EQUIPMENTS[equip_name]
    player[equip_field] = new_equip

    update_player(user_id, player)

    await equip.finish(f"已装备{equip_name}！")


# ========== 魔法系统命令 ==========
@magic.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    action = args.extract_plain_text().strip().split()

    if not action:
        message = show_matrix(user_id)
        await magic.finish(message)

    if action[0] not in ["设置", "重置"]:
        return

    # 配置命令：魔法阵 设置 [槽位] [类型] [名称]
    if action[0] == "设置":
        result = setup_matrix(user_id, action)

    if action[0] == "重置":
        result = setup_matrix(user_id, action)

    await magic.finish(result)


# ========== 战斗系统模块 ==========
@battle.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    player = get_player(user_id)
    final_stats = calculate_final_stats(player)

    # 生成敌人（1-3个）
    enemy_count = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
    enemies = []
    for i in range(0, enemy_count):
        enemy_name = random.choice(list(ENEMIES.keys()))
        enemies.append({
            "name": enemy_name,
            **ENEMIES[enemy_name],  # 深拷贝敌人数据
            "atb": random.randint(0, 50),  # 初始ATB随机值
            "current_hp": ENEMIES[enemy_name]["hp"]
        })

    result_msg = start_battle(user_id, enemies, enemy_count)

    await battle.finish(result_msg)


@attack.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    enemy_name = args.extract_plain_text().strip()
    enemies = []

    if enemy_name not in ENEMIES:
        await attack.finish(f"没有【{enemy_name}】这种敌人，可选敌人：\n{', '.join(ENEMIES.keys())}")

    enemies.append({
        "name": enemy_name,
        **ENEMIES[enemy_name],  # 深拷贝敌人数据
        "atb": random.randint(0, 50),  # 初始ATB随机值
        "current_hp": ENEMIES[enemy_name]["hp"]
    })

    result_msg = start_battle(user_id, enemies, 1, True)

    await attack.finish(result_msg)


# ========== 休息模块 ==========
@rest.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    player = get_player(user_id)
    final_stats = calculate_final_stats(player)

    player["current_hp"] = final_stats["max_hp"]
    player["current_mp"] = final_stats["max_mp"]
    update_player(user_id, player)

    await rest.finish(f"{player['name']}休息了一会，生命值和魔法值已恢复。")


# ========== 锻炼模块 ==========
@exercise.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    player = get_player(user_id)
    ex_type = args.extract_plain_text().strip()

    if ex_type not in EXERCISES:
        info = ""
        for i in EXERCISES.keys():
            info += "\n" + i + "："
            for attr, rate in EXERCISES[i].items():
                info += f"{attr_mapping(attr)}+{int(rate * 100)}%\t"
        message = f"无效锻炼类型，可选：{info}"
        await exercise.finish(message)

    config = EXERCISES[ex_type]

    result = []
    stats = {"base_hp": player["base_hp"], "base_mp": player["base_mp"],
             "base_int": player["base_int"], "base_atn": player["base_atn"],
             "base_spd": player["base_spd"], "base_def": player["base_def"]}
    for attr, rate in config.items():
        base_value = player[attr]
        gain = min(max(math.ceil(base_value * rate), 1), 50)
        player[attr] += gain
        stats[attr] = f"{player[attr]}(+{gain})"

    for attr, rate in stats.items():
        result.append(f"{attr_mapping(attr)}：{stats[attr]}")

    final_stats = calculate_final_stats(player)
    player["current_hp"] = final_stats["max_hp"]
    player["current_mp"] = final_stats["max_mp"]
    result = '\n'.join(result)
    message = f"🏋️ {ex_type}训练完成！\n修炼后基础属性：\n{result}\n"
    update_player(user_id, player)

    await exercise.finish(message)


# ========== 探索模块 ==========
@explore.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    await explore.finish(explore_rusult(user_id))
