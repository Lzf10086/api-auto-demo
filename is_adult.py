def is_adult(age):
    if age < 0:
        raise ValueError("年龄不能为负数")
    return age >= 18
