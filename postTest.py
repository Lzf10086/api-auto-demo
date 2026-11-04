# -*- coding: utf-8 -*-
"""
融销通 接口测试 —— 方法一：post 方法

  接口1  POST http://192.168.5.130:9091/user/login                     登录（拿 token，三个模块都要用）
  接口2  GET  http://192.168.5.130:9091/order/selectSells              个人信息-我卖出的
  接口3  GET  http://192.168.5.130:9091/order/selectBuys               个人信息-我买到的
  接口4  GET  http://192.168.5.130:9091/question/findExpert/{pageNum}   专家模块-专家分页列表
  接口5  GET  http://192.168.5.130:9092/finance/selectByBankId/{pageNum} 银行模块-本行融资申请列表

"""

import sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # 防止中文输出乱码

MAIN = "http://192.168.5.130:9091"   # 融销通主服务（用户/订单/专家/问答）
BANK = "http://192.168.5.130:9092"    # 银行端服务（融资申请审核）

pass_count = 0   # 通过条数
fail_count = 0   # 失败条数
known_count = 0  # 已知缺陷条数（不算失败，但要记到缺陷表）


def check(case_id, title, ok, detail="", known=False):
    """打印一条用例的结果。known=True 表示这是已提交缺陷的现状，不计入失败。"""
    global pass_count, fail_count, known_count
    if known:
        known_count += 1
        print(f"  [{case_id}] 已知缺陷  {title}  ->  {detail}")
    elif ok:
        pass_count += 1
        print(f"  [{case_id}] 通过      {title}")
    else:
        fail_count += 1
        print(f"  [{case_id}] 失败      {title}  ->  {detail}")


def login(username, password, server=MAIN):
    """POST 登录，成功返回 token（data 字段本身就是 JWT，请求头里不要再加 Bearer）"""
    res = requests.post(server + "/user/login",
                        json={"username": username, "password": password},
                        timeout=15)
    return res.json()


def get_json(url, token=None):
    """带 Authorization 头发 GET，返回 (状态码, json)"""
    headers = {}
    if token:
        headers["Authorization"] = token
    res = requests.get(url, headers=headers, timeout=15)
    return res.status_code, res.json()


# ===================== 接口1：POST /user/login 登录 =====================
print("\n=== 接口1  POST /user/login  登录 ===")

js = login("zhangsan", "wyn123456")
print("  实际返回: " + str(js.get("message")) + " / code=" + str(js.get("code")))
check("L-01", "农户账号登录成功", js["flag"] is True and js["code"] == 20000, str(js))
token = js["data"] if js["flag"] else None

js = login("fengj", "wyn123456")
check("L-02", "专家账号登录成功", js["flag"] is True, str(js))
expert_token = js["data"] if js["flag"] else None

js = login("zhangsan", "wrongpassword")
check("L-03", "密码错误被拒绝", js["flag"] is False and js["code"] == 20001, str(js))
print("  提示文案: " + str(js.get("message")))

res = requests.post(MAIN + "/user/login", json={"username": "zhangsan"}, timeout=15)
js = res.json()
check("L-04", "请求体缺 password 字段被拒绝", js.get("flag") is False, str(js))

js = login("buser01", "wyn123456", server=BANK)
check("L-05", "银行账号在银行端(9092)登录成功", js["flag"] is True, str(js))
bank_token = js["data"] if js["flag"] else None

js = login("buser01", "wyn123456", server=MAIN)
check("L-06", "银行账号不能在主服务(9091)登录", js["flag"] is False, str(js))

# ===================== 接口2：GET /order/selectSells 我卖出的 =====================
print("\n=== 接口2  GET /order/selectSells  个人信息-我卖出的 ===")

js = login("zhangxukun", "wyn123456")
seller_token = js["data"]
code, js = get_json(MAIN + "/order/selectSells", seller_token)
print("  实际返回条数: " + str(len(js["data"])) + "，首条: " + str(js["data"][:1]))
check("S-01", "有卖出记录的用户返回其卖出列表", code == 200 and js["flag"] and isinstance(js["data"], list), str(js)[:120])
check("S-02", "列表字段含订单关键字段",
      all(k in js["data"][0] for k in ["purchaseId", "orderId", "sumPrice", "purchaseStatus"]) if js["data"] else False,
      str(js["data"][:1]))

code, js = get_json(MAIN + "/order/selectSells", token)
check("S-03", "无卖出记录的用户返回空数组（结构正确）", js["flag"] and js["data"] == [], str(js))
print("  注意: 空数组时 message 仍是'查询成功'，前端需要有'暂无数据'提示 -> " + str(js.get("message")))

code, js = get_json(MAIN + "/order/selectSells", None)
check("S-04", "不带 token 查我卖出的被拦截", js["flag"] is False and "未登录" in str(js.get("message")), str(js))
check("S-05", "未登录时 HTTP 仍是 200（靠 body 判断）", code == 200, "code=" + str(code))

# ===================== 接口3：GET /order/selectBuys 我买到的 =====================
print("\n=== 接口3  GET /order/selectBuys  个人信息-我买到的 ===")

code, js = get_json(MAIN + "/order/selectBuys", token)
print("  实际返回: " + str(js["data"][:1]))
check("B-01", "查询我买到的订单成功", code == 200 and js["flag"] and isinstance(js["data"], list), str(js)[:120])
check("B-02", "订单字段完整（含金额/状态/时间）",
      all(k in js["data"][0] for k in ["purchaseId", "totalPrice", "purchaseStatus", "createTime"]) if js["data"] else False,
      str(js["data"][:1]))

if js["data"]:
    pid = js["data"][0]["purchaseId"]
    code, js2 = get_json(MAIN + "/order/selectBuysDetail/" + str(pid), token)
    check("B-03", "本人查订单详情成功", js2["flag"] and len(js2["data"]) > 0, str(js2)[:150])

    code, js3 = get_json(MAIN + "/order/selectBuysDetail/" + str(pid), expert_token)
    check("B-04", "别人(专家token)不该查到我的订单详情", js3["flag"] is False or js3["data"] == [], str(js3)[:150],
          known=(js3["flag"] is True and len(js3["data"]) > 0))

code, js = get_json(MAIN + "/order/selectBuys", None)
check("B-05", "不带 token 查我买到的被拦截", js["flag"] is False, str(js))

# ===================== 接口4：GET /question/findExpert/{pageNum} 专家列表 =====================
print("\n=== 接口4  GET /question/findExpert/{pageNum}  专家模块-专家分页 ===")

code, js = get_json(MAIN + "/question/findExpert/1", token)
print("  total=" + str(js["data"]["total"]) + "  本页条数=" + str(len(js["data"]["list"])))
check("E-01", "第1页专家列表查询成功", code == 200 and js["flag"] and js["data"]["total"] > 0, str(js)[:120])
check("E-02", "专家字段完整（账号/姓名/专业/职称/单位）",
      all(k in js["data"]["list"][0] for k in ["userName", "realName", "profession", "position", "belong"]),
      str(js["data"]["list"][:1]))

code, js = get_json(MAIN + "/question/findExpert/999", token)
check("E-03", "页码越界应返回空列表或提示", len(js["data"]["list"]) == 0, "list长度=" + str(len(js["data"]["list"])),
      known=len(js["data"]["list"]) > 0)

code, js = get_json(MAIN + "/question/findExpert/0", token)
check("E-04", "页码为0时不应报500（可接受返回首页）", code == 200 and js.get("flag") is True, str(js)[:120])

try:
    code, js = get_json(MAIN + "/question/findExpert/abc", token)
    print("  页码=abc 实际 HTTP " + str(code) + "，body=" + str(js))
    check("E-05", "页码非数字应返回参数错误提示", "参数" in str(js.get("message")), str(js),
          known=("未登录" in str(js.get("message"))))
except ValueError:
    check("E-05", "页码非数字返回非JSON（500页面）", False, "body 不是 json")

code, js = get_json(MAIN + "/question/findExpert/1", None)
check("E-06", "不带 token 查专家列表被拦截", js["flag"] is False, str(js))

# ===================== 接口5：GET /finance/selectByBankId/{pageNum} 银行融资申请 =====================
print("\n=== 接口5  GET /finance/selectByBankId/{pageNum}  银行模块-本行融资申请 ===")

code, js = get_json(BANK + "/finance/selectByBankId/1", bank_token)
print("  total=" + str(js["data"]["total"]) + "  首条: " + str(js["data"]["list"][:1])[:180])
check("K-01", "银行用户查本行融资申请成功", code == 200 and js["flag"] and js["data"]["total"] > 0, str(js)[:120])
check("K-02", "融资申请含脱敏前的关键字段",
      all(k in js["data"]["list"][0] for k in ["financeId", "ownName", "realName", "money", "status"]),
      str(js["data"]["list"][:1])[:200])
check("K-03", "接口直接返回身份证号等敏感字段（应脱敏）",
      js["data"]["list"][0].get("idNum") in (None, ""),
      "idNum=" + str(js["data"]["list"][0].get("idNum")),
      known=bool(js["data"]["list"][0].get("idNum")))

code, js = get_json(BANK + "/finance/selectByBankId/1", token)
check("K-04", "主服务token不能调银行端接口", js["flag"] is False, str(js))
check("K-04b", "跨端 token 应被优雅拒绝(HTTP 200)", code == 200, "实际 HTTP " + str(code), known=(code == 500))

code, js = get_json(BANK + "/finance/selectByBankId/1", None)
check("K-05", "不带 token 调银行端接口被拦截", js["flag"] is False, str(js))

# ===================== 汇总 =====================
print("\n" + "=" * 60)
print(f"共 {pass_count + fail_count + known_count} 条：通过 {pass_count} 条，失败 {fail_count} 条，命中已知缺陷 {known_count} 条")
print("已知缺陷：")
print("  1) 订单详情 /order/selectBuysDetail/{id} 无归属校验，换别人的 token 也能查到（越权）")
print("  2) 分页页码传非数字返回 HTTP 400 + '您未登录，请先登录'，提示误导（应为参数错误）")
print("  3) 银行端融资申请接口明文返回身份证号 idNum，未脱敏")
print("  4) 格式合法但属于另一服务的 token 调银行端接口，返回 HTTP 500（不带 token 反而 200）")
print("  5) 专家分页页码越界(999)仍返回数据，未做边界处理")
print("=" * 60)
