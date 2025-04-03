import os

localDir = os.path.join(os.path.dirname(__file__), "gachalogs")


def getMeta(need: str):
    gachaTypeDict = {
        "1": "角色活动唤取",
        "2": "武器活动唤取",
        "3": "角色常驻唤取",
        "4": "武器常驻唤取",
        "5": "新手唤取",
        "6": "新手自选唤取",
        "7": "感恩唤取角色",
    }

    data_model = {
        "uid": "",
        "level": "暂时无法评价",
        "count": 0,
        "avg": 0,
        "gechara_display": "none",
        "gechara": "",
        "xbd": 0,
        "wx": 0,
        "jspj": 0,
        "wqpj": 0,
        "chara_display": "block",
        "chara_count": 0,
        "chara_avg": 0,
        "chara_info": "",
        "weapon_display": "block",
        "weapon_count": 0,
        "weapon_avg": 0,
        "weapon_wx": 0,
        "weapon_info": "",
        "czjs_display": "none",
        "czjs_count": 0,
        "czjs_avg": 0,
        "czjs_wx": 0,
        "czjs_info": "",
        "czwq_display": "none",
        "czwq_count": 0,
        "czwq_avg": 0,
        "czwq_wx": 0,
        "czwq_info": "",
        "xsc_display": "none",
        "xsc_count": 0,
        "xsc_avg": 0,
        "xsc_wx": 0,
        "xsc_info": "",
        "zxc_display": "none",
        "zxc_count": 0,
        "zxc_avg": 0,
        "zxc_wx": 0,
        "zxc_info": "",
    }

    gachaMeta = {
        "gachaTypeDict": gachaTypeDict,
        "data_model": data_model,
        "localDir": localDir.replace("\\", "/")
    }
    return gachaMeta[need]
