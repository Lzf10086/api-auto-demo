# 正常路径
import pytest
from jsonschema import validate

POST_SCHEMA = {
    "type" : "object",
    "properties" : {
        "userId" : {"type" : "integer"},
        "id" : {"type" : "integer"},
        "title" : {"type" : "string"},
        "boby" : {"type" : "string"},
    },
    "required" : ["userId","id","title","body"],
}

@pytest.mark.parametrize("post_id",[1,2,3,10,100])
def test_get_single_post_returns_correct_structure(api,post_id):
    """正常路径 + 参数化：按 id 取 post，三层断言"""
    resp = api.get(f"{api.base_url}/posts/{post_id}")

    # 第一层
    assert resp.status_code == 200
    data = resp.json()
    # 第二层
    validate(instance=data,schema=POST_SCHEMA)
    # 第三层
    assert data["id"] == post_id
    assert isinstance(data["title"],str) and data["title"]