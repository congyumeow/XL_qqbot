import os

localDir = os.path.join(os.path.dirname(__file__), "gachalogs")


def getMeta(need: str):
    gachaTypeDict = {
        "11": "角色活动跃迁",
        "12": "光锥活动跃迁",
        "1": "常驻跃迁",
        "2": "新手跃迁",
    }

    data_model = {
        "uid": "",
        "level": "暂时无法评价",
        "count": 0,
        "avg": 0,
        "xbd": 0,
        "wx": 0,
        "jspj": 0,
        "wqpj": 0,
        "xsc_chara": "",
        "xsc_avg": 0,
        "chara_display": "block",
        "chara_count": 0,
        "chara_avg": 0,
        "chara_info": "",
        "weapon_display": "block",
        "weapon_count": 0,
        "weapon_avg": 0,
        "weapon_wx": 0,
        "weapon_info": "",
        "cz_display": "none",
        "cz_count": 0,
        "cz_avg": 0,
        "cz_wx": 0,
        "cz_info": "",
        "xsc_info": "",
    }

    gachaMeta = {
        "gachaTypeDict": gachaTypeDict,
        "data_model": data_model,
        "localDir": localDir.replace("\\", "/")
    }
    return gachaMeta[need]
