# 冒烟：核心接口能通
def test_posts_endpoint_is_reachable(api):
    """冒烟：GET /posts 能通，状态码 200"""
    resp = api.get(f"{api.base_url}/posts")
    assert resp.status_code == 200