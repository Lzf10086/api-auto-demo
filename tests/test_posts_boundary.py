# 边界测试
def test_get_all_post_returns_100_items(api):
    """边界：jsonplaceholder 的 /posts 固定返回100条"""
    resp = api.get(f"{api.base_url}/posts")
    data = resp.json()
    assert len(data) == 100
    assert data[0]["id"] == 1
    assert data[-1]["id"] == 100