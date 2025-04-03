import json
import os.path
import requests
from tinydb import TinyDB, Query

from .__meta__ import getMeta

db_path = os.path.join(os.path.dirname(__file__), "gachalogs/db.json")
db = TinyDB(db_path)
user = Query()

localDir = getMeta("localDir")
gachaTypeDict = getMeta("gachaTypeDict")

GACHALOGS_URL = 'https://gmserver-api.aki-game2.com/gacha/record/query'
tianchong = {
    'cardPoolType': '',
    'count': 1, 'name': '',
    'qualityLevel': "",
    'resourceId': "",
    'resourceType': '',
    'time': ''
}
five_append = {
    'cardPoolType': '',
    'count': 1, 'name': '',
    'qualityLevel': 5,
    'resourceId': "",
    'resourceType': '',
    'time': ''
}


def insert_user_info(qq, uid, record_id):
    gachaFile = f"cache-{uid}.json"
    db.insert({"qq": qq, "uid": uid, "record_id": record_id, "gachaFile": gachaFile})


def query_user_info(qq):
    result = db.search(user.qq == qq)
    if not result:
        return None
    else:
        user_info = {
            "qq": result[0]["qq"],
            "uid": result[0]["uid"],
            "record_id": result[0]["record_id"],
            "gachaFile": result[0]["gachaFile"]
        }
        return user_info


def updata_user_info(qq, gacha_file: str = "", record_id: str = ""):
    if record_id == "":
        db.update({"gachaFile": gacha_file}, user.qq == qq)
    else:
        db.update({"record_id": record_id}, user.qq == qq)


# 数值处理
def num_check(num: int|float):
    num = float(num)
    if num.is_integer():
        num = int(num)
    else:
        num = round(num, 1)
    return num


# 请求头参数设置
def get_request_data(uid, record_id, cardPoolId, cardPoolType):
    return {
         "serverId": "76402e5b20be2c39f095a152090afddc",
         "playerId": uid,
         "languageCode": "zh-Hans",
         "recordId": record_id,
         "cardPoolId": cardPoolId,
         "cardPoolType": cardPoolType
    }


# 检查抽卡连接是否失效
def check_info(uid, record_id):
    request_data = get_request_data(uid, record_id, 1, 1)
    response = requests.post(GACHALOGS_URL, json=request_data, timeout=90)
    body = response.text
    body = json.loads(body)

    if body["message"] != "success":
        return False
    return True


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
def save_gacha_data(qq, data, gacha_log, record_id: str = ""):
    uid = data["uid"]
    gacha_data = data
    gacha_data["gachaLogs"] = gacha_log
    gachaFile = localDir + f"/cache-{uid}.json"
    with open(gachaFile, "w", encoding="utf-8") as f:
        json.dump(gacha_data, f, ensure_ascii=False, indent=2)

    if record_id == "":
        updata_user_info(qq, f"cache-{uid}.json")
    else:
        updata_user_info(qq, f"cache-{uid}.json", record_id)
    return 0


# 获取抽卡记录
def get_gacha_data(uid, record_id):
    gacha_data = {}
    for gachaType in gachaTypeDict:
        request_data = get_request_data(uid, record_id, gachaType, gachaType)
        response = requests.post(GACHALOGS_URL, json=request_data, timeout=90)
        body = response.text
        body = json.loads(body)

        data = body["data"]
        gacha_data[gachaTypeDict[gachaType]] = data

    return gacha_data


# 计算平均值和保底
def sum_avg(gachaType, five_log: list):
    wx_avg = 0
    avg_count = 0
    cost = 0
    yai = 0
    if gachaType == "1":
        for i in five_log:
            if i["name"] != "default":
                if i["name"] in ["安可", "维里奈", "鉴心", "卡卡罗", "凌阳"]:
                    cost += i["cost"]
                    yai += 1
                else:
                    avg_count += 1
                    cost += i["cost"]
                    wx_avg = cost / avg_count
        by = (avg_count - yai) / avg_count * 100
        return num_check(wx_avg), num_check(by)
    else:
        for i in five_log:
            if i["name"] != "default":
                avg_count += 1
                cost += i["cost"]
                wx_avg = cost / avg_count
        return num_check(wx_avg), len(five_log) - 1


# 渲染抽卡记录
def render_gacha_data(uid, gacha_log):
    result = []
    wx = 0
    data = getMeta("data_model")
    data["uid"] = uid
    for gachaType in gachaTypeDict:
        info = gacha_log[gachaTypeDict[gachaType]]
        data["count"] += len(info)
        five_log = []
        now_five = "default"
        now_cost = 0
        for i in info:
            if i["qualityLevel"] == 5:
                five_log.append({"name": now_five, "cost": now_cost})
                now_five = i["name"]
                now_cost = 0
                wx += 1
            now_cost += 1
        five_log.append({"name": now_five, "cost": now_cost})

        match gachaType:
            case "1":
                data["chara_count"] = len(info)
                if len(info) != 0:
                    wx_avg, by = sum_avg(gachaType, five_log)
                    data["chara_avg"] = wx_avg
                    data["jspj"] = wx_avg
                    data["xbd"] = by
                    data["chara_info"] = five_log
                    data["chara_display"] = "block"
            case "2":
                data["weapon_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["weapon_avg"] = wx_avg
                    data["wqpj"] = wx_avg
                    data["weapon_wx"] = wx
                    data["weapon_info"] = five_log
                    data["weapon_display"] = "block"
            case "3":
                data["czjs_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["czjs_avg"] = wx_avg
                    data["czjs_wx"] = wx
                    data["czjs_info"] = five_log
                    data["czjs_display"] = "block"
            case "4":
                data["czwq_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["czwq_avg"] = wx_avg
                    data["czwq_wx"] = wx
                    data["czwq_info"] = five_log
                    data["czwq_display"] = "block"
            case "5":
                data["xsc_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["xsc_avg"] = wx_avg
                    data["xsc_wx"] = wx
                    data["xsc_info"] = five_log
                    data["xsc_display"] = "block"
            case "6":
                data["zxc_count"] = len(info)
                if len(info) != 0:
                    wx_avg, wx = sum_avg(gachaType, five_log)
                    data["zxc_avg"] = wx_avg
                    data["zxc_wx"] = wx
                    data["zxc_info"] = five_log
                    data["zxc_display"] = "block"
            case "7":
                if len(info) != 0:
                    data["gechara_display"] = "block"
                    for i in five_log:
                        if i["name"] != "default":
                            with open("/resource/data.json", "r", encoding="utf-8") as f:
                                data_json = json.load(f)
                        data["gechara"] = data_json[i["name"]]
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
            gachaType = "1"
            info = data["chara_info"]
        case "武器池":
            gachaType = "2"
            info = data["weapon_info"]
        case "常驻角色池":
            gachaType = "3"
            info = data["czjs_info"]
        case "常驻武器池":
            gachaType = "4"
            info = data["czwq_info"]
        case "新手池":
            gachaType = "5"
            info = data["xsc_info"]
        case "新手自选池":
            gachaType = "6"
            info = data["zxc_info"]
        case "感恩角色":
            gachaType = "7"
            info = data["gechara"]

    gachalog = data["gachaLogs"][gachaTypeDict[gachaType]]
    five_log = []
    now_five = "default"
    now_cost = 0
    wx = 0
    for i in gachalog:
        if i["qualityLevel"] == 5:
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
                gachalog.insert(count, tianchong)
        else:
            print("只能修改最后一个角色")
    else:
        five_append["name"] = args[2]
        gachalog.insert(count, five_append)
        for i in range(1, int(args[3])):
            gachalog.append(tianchong)
    new_data = render_gacha_data(data["uid"], data["gachaLogs"])
    save_gacha_data(qq, new_data, data["gachaLogs"])
    return new_data


def merge_gacha_data(old_gachaLog, new_gachaLog):
    merged_gachaLog = {}
    for gachaType in gachaTypeDict:
        old_list = old_gachaLog[gachaTypeDict[gachaType]]
        new_list = new_gachaLog[gachaTypeDict[gachaType]]
        current = 0
        for i in range(0, len(old_list)):
            ot = old_list[i]["time"]
            for j in range(0, len(new_list)):
                nt = new_list[j]["time"]
                if ot == nt:
                    if new_list[j]["name"] == old_list[i]["name"] and \
                            new_list[j]["resourceId"] == old_list[i]["resourceId"]:
                        if new_list[j + 1]["name"] == old_list[i + 1]["name"]:
                            if new_list[j + 1]["resourceId"] == old_list[i + 1]["resourceId"]:
                                current = j
                                break
            break
        merged_list = new_list[:current] + old_list
        merged_gachaLog[gachaTypeDict[gachaType]] = merged_list
    return merged_gachaLog


def get_data(qq):
    user_info = query_user_info(qq)
    data = getMeta("data_model")
    cache = get_local_dataconfig(qq)

    uid = user_info["uid"]
    record_id = user_info["record_id"]
    result = {}
    if cache["msg"] == "未绑定角色!":
        result["msg"] = "未绑定名称角色，请先绑定角色！"
        return result
    elif cache["msg"] == "暂无本地抽卡记录!":
        data["uid"] = uid
        t = check_info(uid, record_id)
        if t:
            gacha_log = get_gacha_data(uid, record_id)
            data = render_gacha_data(uid, gacha_log)
            save_gacha_data(qq, data, gacha_log, record_id)
            result["msg"] = "success"
            result["data"] = data
            return result
        result["msg"] = "抽卡链接失效，且无本地抽卡记录"
        return result
    else:
        data["uid"] = uid
        t = check_info(uid, record_id)
        if t:
            gacha_log = get_gacha_data(uid, record_id)
            old_Log = cache["data"]["gachaLogs"]
            merge_log = merge_gacha_data(old_Log, gacha_log)

            data = render_gacha_data(uid, merge_log)
            save_gacha_data(qq, data, merge_log, record_id)
            result["msg"] = "success"
            result["data"] = data
            return result
        if cache["data"] is not None:
            gacha_log = cache["data"]["gachaLogs"]
            data = render_gacha_data(uid, gacha_log)
            result["msg"] = "success"
            result["data"] = data
        return result


# if __name__ == "__main__":
#     qq = "FAFC9B34D0B135A706808DA7ACE8E628"
#     args = "补充 角色池 今汐 71".split(" ")
#     data = buquan_gachaLogss(qq, args)
#     data = get_data(qq)
#
#     print(data)