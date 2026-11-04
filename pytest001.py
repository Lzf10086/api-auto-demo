# -*- coding: utf-8 -*-
"""
融销通 接口测试 —— 方法二：pytest

模块：银行模块 / 专家模块 / 个人信息模块(我卖出的、我买到的)
5 个接口：POST /user/login、GET /order/selectSells、GET /order/selectBuys、
          GET /question/findExpert/{pageNum}、GET /finance/selectByBankId/{pageNum}(9092)

"""

import pytest
import requests

MAIN = "http://192.168.5.130:9091"
BANK = "http://192.168.5.130:9092"
TOKEN_CACHE = {}   # 同一个账号在本次测试里只登录一次


def login(username, password="wyn123456", server=MAIN):
    """登录并返回 token 字符串；失败直接 assert 报错（前置条件不成立就没必要继续测）"""
    key = server + username
    if key not in TOKEN_CACHE:
        res = requests.post(server + "/user/login",
                            json={"username": username, "password": password},
                            timeout=15)
        js = res.json()
        assert js["flag"] is True, f"前置登录失败：{username} -> {js}"
        TOKEN_CACHE[key] = js["data"]      # data 本身就是 JWT，不加 Bearer
    return TOKEN_CACHE[key]


def get(url, token=None):
    """带 Authorization 头发 GET，返回 json"""
    headers = {}
    if token:
        headers["Authorization"] = token
    res = requests.get(url, headers=headers, timeout=15)
    return res.status_code, res.json()


# ==================== 接口1：POST /user/login ====================

def test_L01_农户账号登录成功():
    res = requests.post(MAIN + "/user/login",
                        json={"username": "zhangsan", "password": "wyn123456"}, timeout=15)
    js = res.json()
    print("\n登录返回：", js)
    assert res.status_code == 200
    assert js["flag"] is True
    assert js["code"] == 20000
    assert js["message"] == "登陆成功"


def test_L02_token是JWT字符串不是对象():
    js = requests.post(MAIN + "/user/login",
                       json={"username": "zhangsan", "password": "wyn123456"}, timeout=15).json()
    assert type(js["data"]) == str
    assert len(js["data"].split(".")) == 3      # JWT 有头.载荷.签名 三段


def test_L03_专家账号登录成功():
    js = requests.post(MAIN + "/user/login",
                       json={"username": "fengj", "password": "wyn123456"}, timeout=15).json()
    assert js["flag"] is True
    assert js["code"] == 20000


def test_L04_密码错误登录失败():
    js = requests.post(MAIN + "/user/login",
                       json={"username": "zhangsan", "password": "wrongpassword"}, timeout=15).json()
    print("\n错误密码返回：", js)
    assert js["flag"] is False
    assert js["code"] == 20001
    assert "data" not in js or js["data"] is None      # 失败不能吐 token


def test_L05_缺少password字段登录失败():
    js = requests.post(MAIN + "/user/login", json={"username": "zhangsan"}, timeout=15).json()
    assert js["flag"] is False


def test_L06_银行账号只能在银行端登录():
    bank_js = requests.post(BANK + "/user/login",
                             json={"username": "buser01", "password": "wyn123456"}, timeout=15).json()
    main_js = requests.post(MAIN + "/user/login",
                             json={"username": "buser01", "password": "wyn123456"}, timeout=15).json()
    assert bank_js["flag"] is True      # 9092 可以
    assert main_js["flag"] is False     # 9091 不行，两套账号体系隔离


# ==================== 接口2：GET /order/selectSells 我卖出的 ====================

def test_S01_有卖出记录的用户返回卖出列表():
    token = login("zhangxukun")
    code, js = get(MAIN + "/order/selectSells", token)
    print("\n我卖出的：", js)
    assert code == 200
    assert js["flag"] is True
    assert type(js["data"]) == list
    assert len(js["data"]) > 0


def test_S02_卖出列表字段完整():
    token = login("zhangxukun")
    code, js = get(MAIN + "/order/selectSells", token)
    first = js["data"][0]
    for field in ["purchaseId", "orderId", "sumPrice", "purchaseStatus", "createTime"]:
        assert field in first, f"缺少字段 {field}"


def test_S03_没有卖出记录时返回空数组():
    token = login("zhangsan")
    code, js = get(MAIN + "/order/selectSells", token)
    assert js["flag"] is True
    assert js["data"] == []


@pytest.mark.xfail(reason="已知体验问题：无数据时 message 仍是'查询成功'，前端需自行给'暂无数据'提示")
def test_S04_无数据时应给出空数据提示文案():
    token = login("zhangsan")
    code, js = get(MAIN + "/order/selectSells", token)
    assert "空" in js["message"] or "暂无" in js["message"]


def test_S05_不带token查我卖出的被拦截():
    code, js = get(MAIN + "/order/selectSells")
    print("\n未登录返回：", js)
    assert js["flag"] is False
    assert "未登录" in js["message"]


def test_S06_未登录时HTTP状态码仍是200():
    """后端不用 401/403 表达鉴权失败，自动化必须断言 body.flag，不能只看 status_code"""
    code, js = get(MAIN + "/order/selectSells")
    assert code == 200
    assert js["flag"] is False


# ==================== 接口3：GET /order/selectBuys 我买到的 ====================

def test_B01_查询我买到的订单成功():
    token = login("zhangsan")
    code, js = get(MAIN + "/order/selectBuys", token)
    print("\n我买到的：", js)
    assert code == 200
    assert js["flag"] is True
    assert type(js["data"]) == list


def test_B02_买到订单字段完整():
    token = login("zhangsan")
    code, js = get(MAIN + "/order/selectBuys", token)
    first = js["data"][0]
    for field in ["purchaseId", "totalPrice", "purchaseStatus", "createTime", "address"]:
        assert field in first, f"缺少字段 {field}"


def test_B03_本人查询订单详情成功():
    token = login("zhangsan")
    code, js = get(MAIN + "/order/selectBuys", token)
    pid = js["data"][0]["purchaseId"]
    code, detail = get(MAIN + "/order/selectBuysDetail/" + str(pid), token)
    print("\n订单详情：", detail)
    assert detail["flag"] is True
    assert len(detail["data"]) > 0
    assert detail["data"][0]["purchaseId"] == pid


@pytest.mark.xfail(reason="已知缺陷(越权)：/order/selectBuysDetail/{id} 无归属校验，别人的 token 也能查到；修复后本条会 xpassed")
def test_B04_他人token查不到我的订单详情():
    my_token = login("zhangsan")
    code, js = get(MAIN + "/order/selectBuys", my_token)
    pid = js["data"][0]["purchaseId"]
    other_token = login("fengj")
    code, leak = get(MAIN + "/order/selectBuysDetail/" + str(pid), other_token)
    print("\n越权查询结果：", leak)
    assert leak["flag"] is False or leak["data"] == []


def test_B05_不带token查我买到的被拦截():
    code, js = get(MAIN + "/order/selectBuys")
    assert js["flag"] is False


# ==================== 接口4：GET /question/findExpert/{pageNum} 专家列表 ====================

def test_E01_专家列表第1页查询成功():
    token = login("zhangsan")
    code, js = get(MAIN + "/question/findExpert/1", token)
    print("\n专家列表 total=", js["data"]["total"])
    assert code == 200
    assert js["flag"] is True
    assert js["data"]["total"] > 0
    assert len(js["data"]["list"]) > 0


def test_E02_专家信息字段完整():
    token = login("zhangsan")
    code, js = get(MAIN + "/question/findExpert/1", token)
    first = js["data"]["list"][0]
    for field in ["userName", "realName", "phone", "profession", "position", "belong"]:
        assert field in first, f"缺少字段 {field}"


def test_E03_每页条数固定为10():
    token = login("zhangsan")
    code, js = get(MAIN + "/question/findExpert/1", token)
    assert len(js["data"]["list"]) <= 10


@pytest.mark.xfail(reason="已知缺陷：页码越界(999)仍返回数据，应返回空 list 或提示")
def test_E04_页码越界应返回空列表():
    token = login("zhangsan")
    code, js = get(MAIN + "/question/findExpert/999", token)
    print("\n越界页返回：", js["data"]["list"])
    assert js["data"]["list"] == []


def test_E05_页码为0不报服务器错误():
    token = login("zhangsan")
    code, js = get(MAIN + "/question/findExpert/0", token)
    assert code == 200
    assert js["flag"] is True


@pytest.mark.xfail(reason="已知缺陷：页码传非数字返回'您未登录，请先登录'，文案误导，应为参数类型错误")
def test_E06_页码非数字应提示参数错误():
    token = login("zhangsan")
    code, js = get(MAIN + "/question/findExpert/abc", token)
    print("\n非数字页码返回：", js)
    assert "参数" in js["message"]


def test_E07_不带token查专家列表被拦截():
    code, js = get(MAIN + "/question/findExpert/1")
    assert js["flag"] is False


# ==================== 接口5：GET /finance/selectByBankId/{pageNum} 银行模块 ====================

def test_K01_银行用户查本行融资申请成功():
    token = login("buser01", server=BANK)
    code, js = get(BANK + "/finance/selectByBankId/1", token)
    print("\n融资申请 total=", js["data"]["total"])
    assert code == 200
    assert js["flag"] is True
    assert js["data"]["total"] > 0


def test_K02_融资申请字段完整():
    token = login("buser01", server=BANK)
    code, js = get(BANK + "/finance/selectByBankId/1", token)
    first = js["data"]["list"][0]
    for field in ["financeId", "ownName", "realName", "phone", "money", "status", "bankId"]:
        assert field in first, f"缺少字段 {field}"


def test_K03_银行端翻页查询正常():
    token = login("buser01", server=BANK)
    code, js = get(BANK + "/finance/selectRecommend/1", token)
    assert js["flag"] is True
    assert type(js["data"]["list"]) == list


@pytest.mark.xfail(reason="已知缺陷(敏感信息)：融资申请列表明文返回 18 位身份证号 idNum，未脱敏")
def test_K04_身份证号应脱敏():
    token = login("buser01", server=BANK)
    code, js = get(BANK + "/finance/selectByBankId/1", token)
    id_num = js["data"]["list"][0]["idNum"] or ""
    print("\nidNum =", id_num)
    assert len(id_num) != 18      # 期望形如 222222**********22 或干脆不返回


def test_K05_主服务token不能调银行端接口():
    token = login("zhangsan")           # 主服务(9091)的 token
    code, js = get(BANK + "/finance/selectByBankId/1", token)
    print("\n跨端调用返回：", code, js)
    assert js["flag"] is False


@pytest.mark.xfail(reason="已知缺陷：格式合法但属于另一服务的 token 会让银行端抛 HTTP 500（无 token 时反而 200），应优雅拒绝")
def test_K07_跨端token应返回200而不是500():
    token = login("zhangsan")
    code, js = get(BANK + "/finance/selectByBankId/1", token)
    assert code == 200, f"实际 HTTP {code}"


def test_K06_不带token调银行端接口被拦截():
    code, js = get(BANK + "/finance/selectByBankId/1")
    assert code == 200                  # 不带 token 是正常走鉴权拦截，返回 200
    assert js["flag"] is False
