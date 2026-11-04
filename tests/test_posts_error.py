# 异常路径
def test_get_nonexistent_post_returns_404(api):
    """异常路径：不存在的id应返回404"""
    resp = api.get(f"{api.base_url}/posts/99999")
    assert resp.status_code == 404