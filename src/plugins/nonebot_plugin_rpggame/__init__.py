import random
import json
import re

from nonebot import on_command
from nonebot.adapters.qq import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .OPMysql import OPMysql
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


# --- 角色管理模块 ---
def get_player(user_id: str):
    """获取玩家数据"""
    data = db.selectOneData(f"SELECT * FROM players WHERE user_id='{user_id}'")  # 注意引号包裹
    if not data:
        return None
    data["weapon"] = json.loads(data["weapon"])
    data["backpack"] = json.loads(data["backpack"])
    data["material"] = json.loads(data["material"])
    data["slots"] = json.loads(data["slots"])
    data["magic_circle"] = json.loads(data["magic_circle"])
    return data


def update_player(user_id: str, data: dict):
    """更新玩家数据"""
    sql = f"""
        UPDATE players SET
        name='{data["name"]}',
        base_hp={data["base_hp"]},
        base_mp={data["base_mp"]},
        base_atn={data["base_atn"]},
        base_int={data["base_int"]},
        base_def={data["base_def"]},
        base_wil={data["base_wil"]},
        base_spd={data["base_spd"]},
        base_dex={data["base_dex"]},
        current_hp={data["current_hp"]},
        current_mp={data["current_mp"]},
        weapon='{json.dumps(data["weapon"], ensure_ascii=False)}',
        gold={data["gold"]},
        backpack='{json.dumps(data["backpack"], ensure_ascii=False)}',
        material='{json.dumps(data["material"], ensure_ascii=False)}',
        slots='{json.dumps(data["slots"], ensure_ascii=False)}',
        magic_circle='{json.dumps(data["magic_circle"], ensure_ascii=False)}'
        WHERE user_id='{user_id}'
        """

    db.insertData(sql)


# 属性计算模块
def calculate_final_stats(player):
    """计算最终属性（包含装备加成）"""
    final = {
        "ATN": player["base_atn"],
        "INT": player["base_int"],
        "DEF": player["base_def"],
        "WIL": player["base_wil"],
        "SPD": player["base_spd"],
        "DEX": player["base_dex"],
        "max_hp": player["base_hp"],
        "max_mp": player["base_mp"]
    }

    # 应用武器加成
    for attr, value in player["weapon"]["attr"].items():
        if attr in ["HP", "MP"]:
            # 百分比加成
            final[f"max_{attr.lower()}"] = int(final[f"max_{attr.lower()}"] * (1 + value))
        else:
            final[attr] += value

    return final


def init_equipment(user_id: str):
    """初始化装备系统"""
    with db.conn.cursor() as cursor:
        # 更新背包和装备
        cursor.execute(
            "UPDATE players SET "
            ""
            "weapon = %s, "
            "armor = %s, "
            "backpack = %s, "
            "material = %s, "
            "slots = %s, "
            "magic_circle = %s"
            "WHERE user_id = %s",
            (
                json.dumps({"name": "匕首", "type": "weapon", "attr": {"ATN": 2, "DEX": 4}}, ensure_ascii=False),
                json.dumps({}),
                json.dumps({"匕首": 1}, ensure_ascii=False),
                json.dumps({}),
                json.dumps({"主力槽": {"main": "", "amplify": "", "focus": "", "power": 0.1},
                            "普通槽": {"main": "", "amplify": "", "focus": "", "power": 0.05, "reduce": 0.07},
                            "辅助槽": {"main": "", "amplify": "", "focus": "", "reduce": 0.15}}, ensure_ascii=False),
                json.dumps({"火焰柱魔法阵": 1}, ensure_ascii=False),
                user_id
            )
        )
    db.conn.commit()


def get_matrix_config(user_id: str) -> dict:
    """获取用户魔法阵配置"""
    data = db.selectOneData(f"SELECT slots FROM players WHERE user_id='{user_id}'")
    return json.loads(data["slots"]) if data else {}


def calculate_magic_effect(config: dict, final_stats) -> tuple:
    """计算魔法效果"""
    total_power, total_cost, power, cost = 0, 0, 0, 0

    # 主魔法阵计算
    if config["main"] != "":
        main = MAGIC_MATRIX[config["main"]]
        power = (main["power"] + final_stats["INT"] * (1 + main["boost"])) * (1 + config.get("power", 0))
        cost = main["cost"] * (1 - config.get("reduce", 0))

    # 增幅魔法阵
    if config["amplify"] != "":
        amp = MAGIC_MATRIX[config["amplify"]]
        power *= (1 + amp["boost"])
        cost *= (1 + amp["reduce"])

    # 凝神魔法阵
    if config["focus"] != "":
        foc = MAGIC_MATRIX[config["focus"]]
        cost *= (1 - foc["reduce"])

    total_power += power
    total_cost += cost

    return int(round(total_power, 0)), int(round(total_cost, 0))


def start_battle(user_id, enemies, enemy_count, is_attack=False):
    player = get_player(user_id)
    final_stats = calculate_final_stats(player)

    # 初始化玩家ATB
    player_atb = {
        "current": random.randint(0, 50),
        "speed": final_stats["SPD"]
    }

    # 战斗过程计算
    battle_log = []

    # ATB循环
    while True:
        # 更新ATB进度
        player_atb["current"] += player_atb["speed"]  # 玩家ATB增速系数

        for enemy in enemies:
            if enemy["current_hp"] > 0:
                enemy["atb"] += enemy["spd"]  # 敌人ATB增速系数

        # 检测可行动单位
        ready_units = []
        if player["current_hp"] > 0 and player_atb["current"] >= 100:
            ready_units.append({"type": "player", "data": player_atb})

        for idx, enemy in enumerate(enemies):
            if enemy["current_hp"] > 0 and enemy["atb"] >= 100:
                ready_units.append({
                    "type": "enemy",
                    "data": enemy,
                    "index": idx
                })

        # 处理行动队列
        while ready_units:
            # 按ATB溢出值排序（模拟时间差）
            ready_units.sort(key=lambda x: (
                -x["data"]["atb"] if x["type"] == "enemy"
                else -player_atb["current"]
            ))

            current_unit = ready_units.pop(0)

            # 玩家行动
            if current_unit["type"] == "player":
                player_atb["current"] -= 100
                # battle_log.append("🚩 你的回合——")

                # 选择目标
                alive_enemies = [e for e in enemies if e["current_hp"] > 0]
                target = random.choice(alive_enemies)

                # 计算伤害
                dmg = int(final_stats["ATN"] * (0.8 + random.random() * 0.4))
                if random.random() < 0.5:
                    magics = []
                    slots = player["slots"]
                    for slot, info in slots.items():
                        if slots[slot]["main"] != "":
                            magics.append(slot)
                    if len(magics) != 0:
                        magic = slots[random.choice(magics)]
                        power, cost = calculate_magic_effect(magic, final_stats)
                        if player["current_mp"] >= cost:
                            dmg = power
                            player["current_mp"] -= cost
                target["current_hp"] -= dmg
                # battle_log.append(f"⚔️ 对{target['name']}造成{dmg}点伤害")

                # 击杀处理
                if target["current_hp"] <= 0:
                    # battle_log.append(f"💀 {target['name']}被消灭！")
                    target["current_hp"] = 0

            # 敌人行动
            else:
                enemy = current_unit["data"]
                enemy["atb"] -= 100
                # battle_log.append(f"☠️ {enemy['name']}的回合——")

                # 计算伤害
                dmg = max(enemy["attack"] - final_stats["DEF"], 0)
                if random.randint(0, 99) < final_stats["DEX"]:
                    dmg = 0
                player["current_hp"] -= dmg
                # battle_log.append(f"💢 对你造成{dmg}点伤害")

                # 死亡检查
                if player["current_hp"] <= 0:
                    # battle_log.append("💀 你已倒下！")
                    player["current_hp"] = 0
                    break

            # 更新存活状态
            alive_enemies = [e for e in enemies if e["current_hp"] > 0]
            if not alive_enemies or player["current_hp"] <= 0:
                break

        # 战斗结束判定
        alive_enemies = [e for e in enemies if e["current_hp"] > 0]
        if not alive_enemies:
            battle_log.append("\n🎉 取得胜利！")
            break
        if player["current_hp"] <= 0:
            battle_log.append("\n💥 战斗失败！")
            break

    # 掉落处理
    total_drops = {}
    if player["current_hp"] > 0:
        for enemy in enemies:
            if enemy["current_hp"] <= 0:
                for item, rate in enemy["drop"].items():
                    if item == "金币":
                        count = random.randint(5, 10) * rate
                        total_drops[item] = total_drops.get(item, 0) + count
                        continue
                    if random.random() < rate:
                        count = random.randint(1, 3)
                        total_drops[item] = total_drops.get(item, 0) + count

    # 更新玩家数据
    if total_drops:
        for item, count in total_drops.items():
            if item == "金币":
                player["gold"] += count
            else:
                player["material"][item] = player["material"].get(item, 0) + count
    player["current_hp"] = max(player["current_hp"], 0)
    update_player(user_id, player)

    # 生成最终消息
    names = []
    for enemy in enemies:
        names.append(enemy["name"])
    enemy_names = "、".join(names) if enemy_count > 1 else enemies[0]["name"]
    if is_attack:
        result_msg = (
            f"{player['name']}向{enemy_names}发起攻击！\n" +
            "\n".join(battle_log) +
            f"\n当前生命：{player['current_hp']}/{calculate_final_stats(player)['max_hp']}"
            f"\n当前魔法：{player['current_mp']}/{calculate_final_stats(player)['max_mp']}"
        )
    else:
        result_msg = (
                f"遭遇{enemy_names}！\n" +
                "\n".join(battle_log) +
                f"\n当前生命：{player['current_hp']}/{calculate_final_stats(player)['max_hp']}"
                f"\n当前魔法：{player['current_mp']}/{calculate_final_stats(player)['max_mp']}"
        )
    if total_drops:
        result_msg += f"\n获得：{', '.join([f'{k}×{v}' for k, v in total_drops.items()])}"

    return result_msg


async def show_matrix(bot: Bot, event: Event, user_id: str):
    """显示当前魔法阵配置"""
    player = get_player(user_id)
    config = get_matrix_config(user_id)
    final_stats = calculate_final_stats(player)
    msg = "🔮 魔法阵配置"

    for slot, parts in config.items():
        info = parts
        power, cost = calculate_magic_effect(info, final_stats)
        slot_info = (
            f"\n{slot}：\n"
            f"🌟主阵：{parts['main']}\n"
            f"🔥增幅：{parts['amplify']}\n"
            f"❄️凝神：{parts['focus']}"
        )
        msg += slot_info
        msg += f"\n威力 {int(power)} | 消耗 {int(cost)}\n"

    await bot.send(event, msg)


def setup_matrix(user_id: str, args: list):
    """配置魔法阵"""
    player = get_player(user_id)
    magics = get_matrix_config(user_id)

    message = ""
    if args[0] == "设置":
        if len(args) > 1:
            args = args[1:]

        if len(args) != 3:
            msg = "格式错误，正确格式：魔法阵 设置 [槽位] [部件类型] [名称]"
            return msg

        slot, part_type, name = args

        # 验证配置有效性
        if slot not in ["主力槽", "普通槽", "辅助槽"]:
            message = "无效槽位类型，可选：主力槽/普通槽/辅助槽"
            return message
        if part_type not in ["主力", "辅助"]:
            message = "无效部件类型，可选：主力/辅助"
            return message
        if name not in player["magic_circle"].keys():
            message = "暂未学习该魔法阵！"
            return message

        # 更新数据库
        if part_type == "辅助":
            if magics[slot] != "":
                message = "请先设置主力魔法阵"
                return message
        part_type = MAGIC_MATRIX[name]["type"]
        magics[slot][part_type] = name
        player["slots"] = magics

        message = f"成功在【{slot}】配置{args[1]}【{name}】"
    if args[0] == "重置":
        if len(args) > 1:
            args = args[1:]

        if len(args) != 1:
            message = "格式错误，正确格式：魔法阵 重置 [槽位]"
            return message

        slot = args[0]

        if slot not in ["主力槽", "普通槽", "辅助槽"]:
            message = "无效槽位类型，可选：主力槽/普通槽/辅助槽"
            return message

        magics[slot]["main"] = ""
        magics[slot]["amplify"] = ""
        magics[slot]["focus"] = ""
        player["slots"] = magics

        message = f"【{slot}】已清除配置"

    update_player(user_id, player)

    return message


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
        "\n📝 输入【我的状态】查看角色信息"
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
        f"💪 力量：{final['ATN']} | 🧠 智力：{final['INT']}\n"
        f"🛡️ 防御：{final['DEF']} | 💫 意志：{final['WIL']}\n"
        f"⚡ 速度：{final['SPD']} | 👐 敏捷：{final['DEX']}\n"
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
    craft_progress = []
    for item, recipe in CRAFT_RECIPES.items():
        can_craft = True
        progress = []
        for mat, need in recipe.items():
            has = player["material"].get(mat, 0)
            progress.append(f"{mat}：{has}/{need}")
            if has < need:
                can_craft = False

        status = "✅" if can_craft else "❌"
        craft_progress.append(f"{status} {item}：" + " | ".join(progress))

    msg = (
            "📦 持有材料：\n" +
            ("\n".join(materials_list) if materials_list else "空空如也") +
            "\n\n🔨 可合成物品：" +
            ("\n" + "\n".join(craft_progress) if craft_progress else "\n暂无足够材料")
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
    item_name = args.extract_plain_text().strip()

    if not item_name:
        # 显示合成列表
        recipes = "\n".join(
            f"{name}: {', '.join(f'{k}×{v}' for k, v in mats.items())}"
            for name, mats in CRAFT_RECIPES.items()
        )
        await craft.finish(f"可合成物品：\n{recipes}")

    if item_name not in CRAFT_RECIPES:
        await craft.finish("没有这个合成配方")

    # 材料检查
    required = CRAFT_RECIPES[item_name]
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
        await show_matrix(bot, event, user_id)
        return

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


@rest.handle()
async def _(bot: Bot, event: Event):
    user_id = event.get_user_id()
    player = get_player(user_id)
    final_stats = calculate_final_stats(player)

    player["current_hp"] = final_stats["max_hp"]
    player["current_mp"] = final_stats["max_mp"]
    update_player(user_id, player)

    await rest.finish(f"{player['name']}休息了一会，生命值和魔法值已恢复。")