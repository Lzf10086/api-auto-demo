import pytest
from is_adult import is_adult

@pytest.mark.parametrize("age,expcted",[
    (17,False),
    (18,True),
    (19,True),
])
def test_is_adult(age,expcted):
    assert is_adult(age) is expcted


# def test_under_18_is_adult():
#     assert is_adult(17) is False
#
# def test_exactly_18_is_adult():
#     assert is_adult(18) is True;
#
# def test_over_18_is_adult():
#     assert is_adult(19) is True;
#
# def test_age_zero_is_adult():
#     assert is_adult(0) is False;
#
# def test_negative_age_raises_error():
#     with pytest.raises(ValueError):
#         is_adult(-1)
