# -*- coding: utf-8 -*-
import scrapy
import re
import json


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['http://www.zhihu.com/']

    # request所需的请求头,否则请求会返回500错误
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    }

    def parse(self, response):
        pass

    def parse_question(self, response):
        pass

    def parse_answer(self, response):
        pass

    def start_requests(self):
        """
        ZhihuSpider的入口,首先在这里进行请求，从登陆页面得到response，并调用login函数
        """
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers, callback=self.login)]

    def login(self, response):
        """
        登陆逻辑执行后调用check_login判断是否登陆成功
        """
        # 使用正则表达式从response里提取xsrf code
        response_text = response.text
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = match_obj.group(1)

        # 得到xsrf code的情况下，才尝试登陆
        if xsrf:
            # 这里以手机号登陆为例
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "13419516267",
                "password": "ssjusher123"
            }
            # 尝试登陆
            return [scrapy.FormRequest(
                url=post_url,
                formdata=post_data,
                headers=self.headers,
                callback=self.check_login
            )]

    def check_login(self, response):
        """
        验证服务器的返回数据判断是否登陆成功,登陆成功则开始爬取数据
        """
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                # 不指定callback,默认调用parse函数
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)

