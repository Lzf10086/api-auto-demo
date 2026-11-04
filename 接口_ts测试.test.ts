/**
 * 融销通 接口测试 —— 方法三：TypeScript + Vitest + axios
 *
 * 模块：银行模块 / 专家模块 / 个人信息模块(我卖出的、我买到的)
 * 5 个接口：POST /user/login、GET /order/selectSells、GET /order/selectBuys、
 *           GET /question/findExpert/{pageNum}、GET /finance/selectByBankId/{pageNum}(9092)
 *

 */
import { describe, it, expect, beforeAll } from 'vitest'
import axios from 'axios'

const MAIN = 'http://192.168.5.130:9091'
const BANK = 'http://192.168.5.130:9092'
const PASS = 'wyn123456'

/** 后端可能返回 400/500 但 body 仍是标准结构，用这个函数保证能拿到 json */
async function getWhatever(url: string, token?: string) {
  return axios.get<ApiResult>(url, {
    headers: token ? { Authorization: token } : {},
    validateStatus: () => true,
  })
}

/** 后端统一返回结构 */
interface ApiResult<T = any> {
  flag: boolean
  code: number
  message: string
  data?: T
}
/** MyBatis 分页结构 */
interface PageData<T> {
  total: number
  list: T[]
}

interface OrderSell {
  sellPurchaseId: number
  purchaseId: number
  orderId: number
  ownName: string
  sumPrice: number
  purchaseStatus: number
  createTime: string
}
interface OrderBuy {
  purchaseId: number
  ownName: string
  totalPrice: number
  purchaseStatus: number
  createTime: string
  address: string
}
interface Expert {
  userName: string
  realName: string
  phone: string
  profession: string
  position: string
  belong: string
}
interface Finance {
  financeId: number
  ownName: string
  realName: string
  phone: string
  idNum: string | null
  money: number
  status: number
  bankId: number
}

/** 登录拿 token；data 本身就是 JWT，请求头不要再拼 Bearer */
async function login(username: string, server: string = MAIN): Promise<string> {
  const res = await axios.post<ApiResult<string>>(server + '/user/login', { username, password: PASS })
  expect(res.data.flag).toBe(true)
  return res.data.data as string
}

/** 带 token 的 GET：鉴权头只有 Authorization 这一个，值就是裸 token */
function authHeader(token: string) {
  return { headers: { Authorization: token } }
}

const tokens = { farmer: '', expert: '', seller: '', bank: '' }
let buyOrderId = 0

beforeAll(async () => {
  tokens.farmer = await login('zhangsan')
  tokens.expert = await login('fengj')
  tokens.seller = await login('zhangxukun')
  tokens.bank = await login('buser01', BANK)
  const buys = await axios.get<ApiResult<OrderBuy[]>>(MAIN + '/order/selectBuys', authHeader(tokens.farmer))
  buyOrderId = buys.data.data?.[0]?.purchaseId ?? 0
})

// ==================== 接口1：POST /user/login ====================
describe('接口1 POST /user/login 登录', () => {
  it('农户账号登录成功，返回 code 20000', async () => {
    const res = await axios.post<ApiResult<string>>(MAIN + '/user/login', { username: 'zhangsan', password: PASS })
    expect(res.status).toBe(200)
    expect(res.data.flag).toBe(true)
    expect(res.data.code).toBe(20000)
  })

  it('token 是三段式 JWT 字符串', async () => {
    const res = await axios.post<ApiResult<string>>(MAIN + '/user/login', { username: 'zhangsan', password: PASS })
    expect(typeof res.data.data).toBe('string')
    expect((res.data.data as string).split('.')).toHaveLength(3)
  })

  it('密码错误时 flag=false / code=20001，且不发 token', async () => {
    const res = await axios.post<ApiResult>(MAIN + '/user/login', { username: 'zhangsan', password: 'wrongpassword' })
    expect(res.data.flag).toBe(false)
    expect(res.data.code).toBe(20001)
    expect(res.data.data).toBeUndefined()
  })

  it('请求体缺 password 字段登录失败', async () => {
    const res = await axios.post<ApiResult>(MAIN + '/user/login', { username: 'zhangsan' })
    expect(res.data.flag).toBe(false)
  })

  it('银行账号只能在银行端(9092)登录', async () => {
    const okAtBank = await axios.post<ApiResult>(BANK + '/user/login', { username: 'buser01', password: PASS })
    const failAtMain = await axios.post<ApiResult>(MAIN + '/user/login', { username: 'buser01', password: PASS })
    expect(okAtBank.data.flag).toBe(true)
    expect(failAtMain.data.flag).toBe(false)
  })
})

// ==================== 接口2：GET /order/selectSells ====================
describe('接口2 GET /order/selectSells 我卖出的', () => {
  it('有卖出记录的用户返回非空数组', async () => {
    const res = await axios.get<ApiResult<OrderSell[]>>(MAIN + '/order/selectSells', authHeader(tokens.seller))
    expect(res.data.flag).toBe(true)
    expect(Array.isArray(res.data.data)).toBe(true)
    expect(res.data.data!.length).toBeGreaterThan(0)
  })

  it('卖出记录字段完整', async () => {
    const res = await axios.get<ApiResult<OrderSell[]>>(MAIN + '/order/selectSells', authHeader(tokens.seller))
    const first = res.data.data![0]
    for (const key of ['purchaseId', 'orderId', 'sumPrice', 'purchaseStatus', 'createTime']) {
      expect(first).toHaveProperty(key)
    }
  })

  it('无卖出记录返回空数组', async () => {
    const res = await axios.get<ApiResult<OrderSell[]>>(MAIN + '/order/selectSells', authHeader(tokens.farmer))
    expect(res.data.data).toEqual([])
  })

  it('不带 token 被拦截，提示未登录（HTTP 仍是 200）', async () => {
    const res = await axios.get<ApiResult>(MAIN + '/order/selectSells')
    expect(res.status).toBe(200)
    expect(res.data.flag).toBe(false)
    expect(res.data.message).toContain('未登录')
  })

  it.fails('已知体验问题：无数据时 message 应提示"暂无数据"而不是"查询成功"', async () => {
    const res = await axios.get<ApiResult<OrderSell[]>>(MAIN + '/order/selectSells', authHeader(tokens.farmer))
    expect(res.data.message).toContain('暂无')
  })
})

// ==================== 接口3：GET /order/selectBuys ====================
describe('接口3 GET /order/selectBuys 我买到的', () => {
  it('查询我买到的订单成功', async () => {
    const res = await axios.get<ApiResult<OrderBuy[]>>(MAIN + '/order/selectBuys', authHeader(tokens.farmer))
    expect(res.data.flag).toBe(true)
    expect(res.data.data!.length).toBeGreaterThan(0)
  })

  it('买到订单字段完整', async () => {
    const res = await axios.get<ApiResult<OrderBuy[]>>(MAIN + '/order/selectBuys', authHeader(tokens.farmer))
    const first = res.data.data![0]
    for (const key of ['purchaseId', 'totalPrice', 'purchaseStatus', 'createTime', 'address']) {
      expect(first).toHaveProperty(key)
    }
  })

  it('本人查询订单详情成功', async () => {
    expect(buyOrderId).toBeGreaterThan(0)
    const res = await axios.get<ApiResult<any[]>>(`${MAIN}/order/selectBuysDetail/${buyOrderId}`, authHeader(tokens.farmer))
    expect(res.data.flag).toBe(true)
    expect(res.data.data![0].purchaseId).toBe(buyOrderId)
  })

  it.fails('已知缺陷(越权)：他人 token 不应查到我的订单详情', async () => {
    const res = await axios.get<ApiResult<any[]>>(`${MAIN}/order/selectBuysDetail/${buyOrderId}`, authHeader(tokens.expert))
    expect(res.data.flag).toBe(false)
  })

  it('不带 token 被拦截', async () => {
    const res = await axios.get<ApiResult>(MAIN + '/order/selectBuys')
    expect(res.data.flag).toBe(false)
  })
})

// ==================== 接口4：GET /question/findExpert/{pageNum} ====================
describe('接口4 GET /question/findExpert/{pageNum} 专家列表', () => {
  it('第 1 页专家查询成功', async () => {
    const res = await axios.get<ApiResult<PageData<Expert>>>(MAIN + '/question/findExpert/1', authHeader(tokens.farmer))
    expect(res.data.flag).toBe(true)
    expect(res.data.data!.total).toBeGreaterThan(0)
  })

  it('专家信息字段完整（姓名/专业/职称/单位）', async () => {
    const res = await axios.get<ApiResult<PageData<Expert>>>(MAIN + '/question/findExpert/1', authHeader(tokens.farmer))
    const first = res.data.data!.list[0]
    for (const key of ['userName', 'realName', 'phone', 'profession', 'position', 'belong']) {
      expect(first).toHaveProperty(key)
    }
  })

  it('每页最多 10 条', async () => {
    const res = await axios.get<ApiResult<PageData<Expert>>>(MAIN + '/question/findExpert/1', authHeader(tokens.farmer))
    expect(res.data.data!.list.length).toBeLessThanOrEqual(10)
  })

  it.fails('已知缺陷：页码越界(999)仍返回数据，应返回空 list', async () => {
    const res = await axios.get<ApiResult<PageData<Expert>>>(MAIN + '/question/findExpert/999', authHeader(tokens.farmer))
    expect(res.data.data!.list).toEqual([])
  })

  it.fails('已知缺陷：页码非数字应提示参数错误，现在提示"未登录"（HTTP 400）', async () => {
    const res = await getWhatever(MAIN + '/question/findExpert/abc', tokens.farmer)
    expect(res.data.message).toContain('参数')
  })

  it('不带 token 被拦截', async () => {
    const res = await axios.get<ApiResult>(MAIN + '/question/findExpert/1')
    expect(res.data.flag).toBe(false)
  })
})

// ==================== 接口5：GET /finance/selectByBankId/{pageNum}（银行端 9092） ====================
describe('接口5 GET /finance/selectByBankId/{pageNum} 银行融资申请', () => {
  it('银行用户查询本行融资申请成功', async () => {
    const res = await axios.get<ApiResult<PageData<Finance>>>(BANK + '/finance/selectByBankId/1', authHeader(tokens.bank))
    expect(res.data.flag).toBe(true)
    expect(res.data.data!.total).toBeGreaterThan(0)
  })

  it('融资申请字段完整', async () => {
    const res = await axios.get<ApiResult<PageData<Finance>>>(BANK + '/finance/selectByBankId/1', authHeader(tokens.bank))
    const first = res.data.data!.list[0]
    for (const key of ['financeId', 'ownName', 'realName', 'phone', 'money', 'status', 'bankId']) {
      expect(first).toHaveProperty(key)
    }
  })

  it.fails('已知缺陷(敏感信息)：身份证号 idNum 明文返回，应脱敏', async () => {
    const res = await axios.get<ApiResult<PageData<Finance>>>(BANK + '/finance/selectByBankId/1', authHeader(tokens.bank))
    expect(res.data.data!.list[0].idNum ?? '').not.toMatch(/^\d{18}$/)
  })

  it('主服务 token 不能调用银行端接口（跨端 token 不通用）', async () => {
    const res = await getWhatever(BANK + '/finance/selectByBankId/1', tokens.farmer)
    expect(res.data.flag).toBe(false)
    expect(res.data.message).toContain('未登录')
  })

  it.fails('已知缺陷：格式合法但属于另一服务的 token 让银行端抛 HTTP 500（应优雅返回 200+flag:false）', async () => {
    const res = await getWhatever(BANK + '/finance/selectByBankId/1', tokens.farmer)
    expect(res.status).toBe(200)
  })

  it('不带 token 调用银行端接口被拦截（HTTP 200 + flag:false）', async () => {
    const res = await getWhatever(BANK + '/finance/selectByBankId/1')
    expect(res.status).toBe(200)
    expect(res.data.flag).toBe(false)
  })
})
