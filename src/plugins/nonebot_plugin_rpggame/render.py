import random

from .OPMysql import OPMysql
from .config import *
import json

db = OPMysql()

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
        base_spd={data["base_spd"]},
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
        "SPD": player["base_spd"],
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
                json.dumps({"name": "匕首", "type": "weapon", "attr": {"ATN": 2, "SPD": 4}}, ensure_ascii=False),
                json.dumps({}),
                json.dumps({"匕首": 1}, ensure_ascii=False),
                json.dumps({}),
                json.dumps({"主力槽": {"main": "火焰柱魔法阵", "amplify": "", "focus": "", "power": 0.1},
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
                if random.randint(0, 99) < final_stats["DEF"]:
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
                        count = 1
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


def show_matrix(user_id: str):
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

    return msg


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


def attr_mapping(attr: str) -> str:
    """属性名称映射"""
    return {
        "base_atn": "力量",
        "base_def": "防御",
        "base_spd": "敏捷",
        "base_hp": "生命",
        "base_int": "魔力",
        "base_mp": "法力"
    }.get(attr, attr)


def explore(user_id: str) -> str:
    player = get_player(user_id)
    message = ""

    total_drops = {}
    for i in range(0, 2):
        material_name = random.choice(list(ITEMS.keys()))
        total_drops[material_name] = random.randint(1, 3)

    for item, count in total_drops.items():
        player["material"][item] = player["material"].get(item, 0) + count

    message += f"\n获得：{', '.join([f'{k}×{v}' for k, v in total_drops.items()])}"
    update_player(user_id, player)

    return message
