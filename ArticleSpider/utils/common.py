# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
import re
__author__ = 'shishengjia'


def get_md5(url):
    """
    生成MD5值
    """
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def extract_num(text):
    """
    从字符串中提取出数字
    """
    match_re = re.match(".*?(\d+).*", text)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


def date_convert(value):
    """
        将字符串转为date对象
        自定义方法比datetime.strptime()的效率要高，但前提是日期的格式必须确定
        这里已经分析过文章，已经知道得到日期的格式
    """
    try:
        year, month, day = value.split('/')
        create_date = datetime(int(year), int(month), int(day)).date()
    except Exception as e:
        create_date = datetime.now().date()

    return create_date


if __name__ == "__main__":
    print (get_md5("http://jobbole.com".encode("utf-8")))