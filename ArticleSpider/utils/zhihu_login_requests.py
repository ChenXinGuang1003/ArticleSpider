# -*- encoding: utf-8 -*-
from PIL import Image
import requests
import re
import time
try:
    import cookielib
except:
    import http.cookiejar as cookielib
_author_ = 'shishengjia'
_date_ = '2017/3/30 13:18'

"""
模拟知乎登陆，这里使用手动打码来实现登陆
在登陆过程中，会发送几次请求，一次是获取_xsrf，一次是获取验证码图片，如果用request将会产生不同的cookies，导致登陆失败，所以使用
session来管理cookies
"""


session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print("cookie未能加载")

# 构建请求头
headers = {
    "HOST":"www.zhihu.com",
    "Referer": "https://www.zhizhu.com",
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
}


def get_captcha():
    """
    获取验证码并手动输入
    """
    # 构建随机数字串
    numbers = str(int(time.time()*1000))
    url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(numbers)
    response = session.get(url, headers=headers)
    with open("captcha.jpg", "wb") as f:
        f.write(response.content)

    try:
        # 显示验证码
        im = Image.open("captcha.jpg")
        im.show()
        im.close()
    except Exception as e:
        print(e)

    captcha = input("请手动输入验证码:")
    return captcha


def get_xsrf():
    """
    正则表达式从网页内容获取_xsrf
    """
    response = session.get("https://www.zhihu.com", headers=headers)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text)
    if match_obj:
        return match_obj.group(1)
    else:
        return ""


def is_login():
    """
    通过请求个人中心页面返回的状态码来判断是否为登录状态
    """
    inbox_url = "https://www.zhihu.com/question/56250357/answer/148534773"
    # allow_redirects设置为False，防止未登陆状态下重定向到登陆页面返回200
    response = session.get(inbox_url, headers=headers, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def get_index():
    # 获取首页
    response = session.get("https://www.zhihu.com", headers=headers)
    with open("index_page.html", "wb") as f:
        f.write(response.text.encode("utf-8"))
    print("ok")


def zhihu_login(account, password):
    """
    知乎登陆
    """
    post_url = ""
    post_data = {}
    if re.match("^1\d{10}",account):
        print("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": account,
            "password": password,
            "captcha": get_captcha()
        }
    else:
        if "@" in account:
            # 判断用户名是否为邮箱
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "email": account,
                "password": password
            }

    response = session.post(post_url, data=post_data, headers=headers)
    session.cookies.save()

zhihu_login("13419516267", "ssjusher123")
is_login()
