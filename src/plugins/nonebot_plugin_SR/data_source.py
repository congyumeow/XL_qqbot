import json
import os.path
import re

import requests
from time import time
from datetime import datetime
from tinydb import TinyDB, Query

from .__meta__ import getMeta

db_path = os.path.join(os.path.dirname(__file__), "gachalogs/db.json")
db = TinyDB(db_path)
user = Query()

localDir = getMeta("localDir")
gachaTypeDict = getMeta("gachaTypeDict")

tianchong = {
    "gacha_id": "",
    "item_id": "",
    "count": "1",
    "time": "",
    "name": "",
    "item_type": "",
    "rank_type": "",
    "gacha_type": "",
    "id": ""
}
five_append = {
    "gacha_id": "",
    "item_id": "",
    "count": "1",
    "time": "",
    "name": "",
    "item_type": "",
    "rank_type": "5",
    "gacha_type": "",
    "id": ""
}


def insert_user_info(qq, uid, authkey):
    gachaFile = f"cache-{uid}.json"
    db.insert({"qq": qq, "uid": uid, "gachaFile": gachaFile, "authkey": authkey})


def query_user_info(qq):
    result = db.search(user.qq == qq)
    if not result:
        return None
    else:
        user_info = {
            "qq": result[0]["qq"],
            "uid": result[0]["uid"],
            "authkey": result[0]["authkey"],
            "gachaFile": result[0]["gachaFile"]
        }
        return user_info


def updata_user_info(qq, gacha_file: str = "", authkey: str = ""):
    if authkey == "":
        db.update({"gachaFile": gacha_file}, user.qq == qq)
    else:
        db.update({"authkey": authkey}, user.qq == qq)


# 数值处理
def num_check(num: int|float):
    num = float(num)
    if num.is_integer():
        num = int(num)
    else:
        num = round(num, 1)
    return num


def eu_af_level(data: dict):
    if data["avg"] <= 40:
        data["level"] = "千里挑一至尊欧皇"
    elif 40 < data["avg"] <= 80:
        data["level"] = "欧气满满大欧皇"
    elif 80 < data["avg"] <= 120:
        data["level"] = "平平无奇普通人"
    elif 120 < data["avg"] <= 160:
        data["level"] = "欧气不足小非酋"
    elif 160 < data["avg"] <= 180:
        data["level"] = "千里挑一大非酋"
    return data


# 检查抽卡连接是否失效
def check_info(url):
    response = requests.get(url)
    body = response.text
    body = json.loads(body)
    message = body["message"]
    if message == "authkey timeout":
        return "抽卡链接 AuthKey 已经失效，尝试返回缓存内容..."
    elif message == "OK":
        return "成功"
    else:
        return "抽卡链接错误" + message


# 读取本地抽卡记录
def get_local_dataconfig(qq):
    user_info = query_user_info(qq)
    cache = {"msg": "", "data": {}}
    if user_info is None:
        cache["msg"] = "未绑定角色!"
        cache["data"] = {}
        return cache
    gachaFile = localDir + f"/{user_info['gachaFile']}"
    if not os.path.isfile(gachaFile):
        cache["msg"] = "暂无本地抽卡记录!"
        cache["data"] = {}
        return cache
    cache["msg"] = user_info["gachaFile"]
    with open(gachaFile, "r", encoding="utf-8") as f:
        cache["data"] = json.load(f)
    return cache


# 保存抽卡记录
def save_gacha_data(qq, data, gacha_log, authkey: str = ""):
    uid = data["uid"]
    gacha_data = data
    gacha_data["gachaLogs"] = gacha_log
    gachaFile = localDir + f"/cache-{uid}.json"
    with open(gachaFile, "w", encoding="utf-8") as f:
        json.dump(gacha_data, f, ensure_ascii=False, indent=2)

    if authkey == "":
        updata_user_info(qq, f"cache-{uid}.json")
    else:
        updata_user_info(qq, f"cache-{uid}.json", authkey)
    return 0


# 获取抽卡记录
def get_gacha_data(authkey):
    url = "https://public-operation-hkrpg.mihoyo.com/common/gacha_record/api/getGachaLog?" \
           "authkey_ver=1&sign_type=2&auth_appid=webview_gacha&win_mode=fullscreen&" \
           "gacha_id=374b7481f4f39bcd526631139cccc1aa27f7a8f3&timestamp=1744155064&region=prod_gf_cn&default_gacha_type=11" \
           "&decide_item_id_list=1208%252C1205%252C1101%252C1104%252C1102%252C1209%252C1211&lang=zh-cn&plat_type=pc&" \
           "authkey={}&game_biz=hkrpg_cn&os_system=Windows%2011%20%20%2810.0.22631%29%2064bit&" \
           "device_model=System%20Product%20Name%20%28ASUS%29&page=1&size=20&gacha_type=11&end_id=0".format(authkey)
    gachaData = {
        "uid": "",
        "time": "",
        "url": "",
        "gachaLogs": {
            "11": [],
            "12": [],
            "1": [],
            "2": [],
        }
    }
    heards = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    for gachaType in gachaTypeDict:
        result = []
        page = 1
        end_id = 0
        while True:
            url = re.sub(r'(gacha_type=)\d+', r'\g<1>{}'.format(gachaType), url)
            url = re.sub(r'page=(.*?)&', "page={}&".format(page), url)
            url = re.sub(r'end_id=(.*?)\d+', "end_id={}".format(end_id), url)
            response = requests.get(url, headers=heards)
            body = response.text
            body = json.loads(body)
            data = body["data"]['list']
            print("正在获取{}第{}页记录".format(gachaTypeDict[gachaType], page))
            result.extend(data)
            page += 1
            if len(data) == 20:
                end_id = data[19]["id"]
            if 1 <= len(data) < 20:
                res = []
                for i in result:
                    rex = {}
                    rex["gacha_id"] = i["gacha_id"]
                    rex["item_id"] = i["item_id"]
                    rex["count"] = i["count"]
                    rex["time"] = i["time"]
                    rex["name"] = i["name"]
                    rex["item_type"] = i["item_type"]
                    rex["rank_type"] = i["rank_type"]
                    rex["gacha_type"] = i["gacha_type"]
                    rex["id"] = i["id"]
                    uid = i["uid"]
                    res.append(rex)
                gachaData["uid"] = uid
                gachaData["time"] = int(time())
                gachaData["url"] = url
                gachaData["gachaLogs"][gachaType] = res
            if len(data) == 0 or len(data) < 20:
                break
    return gachaData


# 计算平均值和保底
def sum_avg(gachaType, five_log: list):
    wx_avg = 0
    avg_count = 0
    cost = 0
    wai = 0
    if gachaType == "11":
        for i in five_log:
            if i["name"] != "default":
                if i["name"] in ["布洛妮娅", "杰帕德", "彦卿", "白露", "克拉拉", "瓦尔特", "姬子"]:
                    cost += i["cost"]
                    wai += 1
                if i["name"] in ["刃", "符玄", "希儿"]:
                    time1 = datetime.strptime(i["time"], "%Y-%m-%d %H:%M:%S")
                    time2 = datetime.strptime("2025-04-21 06:00:00", "%Y-%m-%d %H:%M:%S")
                    if time1 > time2:
                        cost += i["cost"]
                        wai += 1
                else:
                    avg_count += 1
                    cost += i["cost"]
                    wx_avg = cost / avg_count
        by = (avg_count - wai) / avg_count * 100
        return num_check(wx_avg), num_check(by)
    elif gachaType == "12":
        for i in five_log:
            if i["name"] != "default":
                if i["name"] in ["银河铁道之夜", "无可取代额东西", "但战斗还未结束", "以世界之名", "制胜的瞬间", "如泥酣眠", "时节不居"]:
                    cost += i["cost"]
                    wai += 1
                else:
                    avg_count += 1
                    cost += i["cost"]
                    wx_avg = cost / avg_count
        by = (avg_count - wai) / avg_count * 100
        return num_check(wx_avg), num_check(by)
    else:
        for i in five_log:
            if i["name"] != "default":
                avg_count += 1
                cost += i["cost"]
                wx_avg = cost / avg_count
        return num_check(wx_avg), len(five_log) - 1
    


# 渲染抽卡记录
def render_gacha_data(gacha_log):
    result = []
    wx = 0
    data = getMeta("data_model")
    data["uid"] = gacha_log["uid"]
    for gachaType in gachaTypeDict:
        info = gacha_log["gachaLogs"][gachaType]
        data["count"] += len(info)
        five_log = []
        now_five = "default"
        now_cost = 0
        five_time = ""
        for i in info:
            if i["rank_type"] == "5":
                five_log.append({"name": now_five, "cost": now_cost, "time": five_time})
                now_five = i["name"]
                now_cost = 0
                wx += 1
                five_time = i["time"]
            now_cost += 1
        five_log.append({"name": now_five, "cost": now_cost, "time": five_time})

        match gachaType:
            case "11":
                data["chara_count"] = len(info)
                if len(info) != 0:
                    wx_avg, by = sum_avg(gachaType, five_log)
                    data["chara_avg"] = wx_avg
                    data["jspj"] = wx_avg
                    data["xbd"] = by
                    data["chara_info"] = five_log
                    data["chara_display"] = "block"
            case "12":
                data["weapon_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["weapon_avg"] = wx_avg
                    data["wqpj"] = wx_avg
                    data["weapon_bw"] = wx
                    data["weapon_info"] = five_log
                    data["weapon_display"] = "block"
            case "1":
                data["cz_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["cz_avg"] = wx_avg
                    data["cz_wx"] = wx
                    data["cz_info"] = five_log
                    data["cz_display"] = "block"
            case "2":
                data["xsc_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    for i in five_log:
                        if i["name"] != "default":
                            data["xsc_chara"] = f'{i["name"]}.png'
                            data["xsc_avg"] = wx_avg
                            data["xsc_info"] = five_log
        for i in five_log:
            if i["name"] != "default":
                result.append(i)

        count_avg = sum_avg("2", result)
        data["avg"] = count_avg[0]
        data["wx"] = len(result)

    return data


# 手动补全抽卡记录
def buquan_gachaLogss(qq, args):
    # arg = ["修改", "角色池", "卡卡罗", 68]
    cache = get_local_dataconfig(qq)
    data = cache["data"]
    gachaType = ""
    info = []
    match args[1]:
        case "角色池":
            gachaType = "11"
            info = data["chara_info"]
        case "光锥池":
            gachaType = "12"
            info = data["weapon_info"]
        case "常驻池":
            gachaType = "1"
            info = data["cz_info"]
        case "新手池":
            gachaType = "2"
            info = data["xsc_info"]

    gachalog = data["gachaLogs"]["gachaLogs"][gachaType]
    five_log = []
    now_five = "default"
    now_cost = 0
    wx = 0
    for i in gachalog:
        if i["rank_type"] == "5":
            five_log.append({"name": now_five, "cost": now_cost})
            now_five = i["name"]
            now_cost = 0
            wx += 1
        now_cost += 1
    five_log.append({"name": now_five, "cost": now_cost})
    count = 0
    for i in five_log:
        count += i["cost"]
    if args[0] == "修改":
        last = five_log[len(info) - 1]
        if last["name"] == args[2]:
            length = int(args[3]) - last["cost"]
            for item in range(0, length):
                tianchong["gacha_type"] = gachaType
                gachalog.insert(count, tianchong)
        else:
            print("只能修改最后一个角色")
    else:
        five_append["name"] = args[2]
        five_append["gacha_type"] = gachaType
        gachalog.insert(count, five_append)
        for i in range(1, int(args[3])):
            tianchong["gacha_type"] = gachaType
            gachalog.append(tianchong)
    new_data = render_gacha_data(data["gachaLogs"])
    new_data = eu_af_level(new_data)
    save_gacha_data(qq, new_data, data["gachaLogs"])
    return new_data


def merge_gacha_data(old_gachaLog, new_gachaLog):
    merged_gachaLog = {
        "uid": old_gachaLog["uid"],
        "time": old_gachaLog["time"],
        "url": old_gachaLog["url"],
        "gachaLogs": {
            "11": [],
            "12": [],
            "1": [],
            "2": [],
        }
    }

    for gachaType in gachaTypeDict:
        old_list = old_gachaLog["gachaLogs"][gachaType]
        new_list = new_gachaLog["gachaLogs"][gachaType]
        current = 0
        for i in range(0, len(old_list)):
            ot = old_list[i]["time"]
            for j in range(0, len(new_list)):
                nt = new_list[j]["time"]
                if ot == nt:
                    if new_list[j]["name"] == old_list[i]["name"] and new_list[j]["id"] == old_list[i]["id"]:
                        if new_list[j + 1]["name"] == old_list[i + 1]["name"] and \
                            new_list[j + 1]["id"] == old_list[i + 1]["id"]:
                                current = j
                                break
            break
        merged_list = new_list[:current] + old_list
        merged_gachaLog["gachaLogs"][gachaType] = merged_list
    return merged_gachaLog


def get_data(qq):
    user_info = query_user_info(qq)
    data = getMeta("data_model")
    cache = get_local_dataconfig(qq)

    url = "https://public-operation-hkrpg.mihoyo.com/common/gacha_record/api/getGachaLog?" \
           "authkey_ver=1&sign_type=2&auth_appid=webview_gacha&win_mode=fullscreen&" \
           "gacha_id=374b7481f4f39bcd526631139cccc1aa27f7a8f3&timestamp=1744155064&region=prod_gf_cn&" \
           "default_gacha_type=11&decide_item_id_list=1208%252C1205%252C1101%252C1104%252C1102%252C1209%252C1211&" \
           "lang=zh-cn&plat_type=pc&authkey={}&game_biz=hkrpg_cn&os_system=Windows%2011%20%20%2810.0.22631%29%2064bit&" \
           "device_model=System%20Product%20Name%20%28ASUS%29&page=1&size=5&gacha_type=11"

    result = {}
    authkey = user_info["authkey"]
    if cache["msg"] == "未绑定角色!":
        result["msg"] = "未绑定名称角色，请先绑定角色！"
        return result
    elif cache["msg"] == "暂无本地抽卡记录!":
        t = check_info(url.format(authkey))
        if t == "成功":
            gacha_log = get_gacha_data(authkey)
            data = render_gacha_data(gacha_log)
            data = eu_af_level(data)
            save_gacha_data(qq, data, gacha_log)
            result["msg"] = "success"
            result["data"] = data
            return result
        result["msg"] = "抽卡链接失效，且无本地抽卡记录"
        return result
    else:
        t = check_info(url.format(authkey))
        if t == "成功":
            gacha_log = get_gacha_data(authkey)
            old_Log = cache["data"]["gachaLogs"]
            merge_log = merge_gacha_data(old_Log, gacha_log)

            data = render_gacha_data(merge_log)
            data = eu_af_level(data)
            save_gacha_data(qq, data, merge_log)
            result["msg"] = "success"
            result["data"] = data
            return result
        if cache["data"] is not None:
            gacha_log = cache["data"]["gachaLogs"]
            data = render_gacha_data(gacha_log)
            result["msg"] = "success"
            result["data"] = data
        return result
