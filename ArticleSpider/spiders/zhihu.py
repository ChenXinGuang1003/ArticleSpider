# -*- coding: utf-8 -*-
from datetime import datetime
from PIL import Image
import scrapy
import re
import json
import time
try:
    # Python3
    from urllib import parse
except:
    # Python2
    import urlparse as parse

from items import ZhihuAnswerItem, ZhihuQuestionItem
from scrapy.loader import ItemLoader


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    # request所需的请求头,否则请求会返回500错误
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    }

    custom_settings = {
        'COOKIES_ENABLED': True
    }

    def parse(self, response):
        """
        提取知乎首页的全部url，并过滤出格式为/question/XXXXXX的url
        """
        all_urls = response.css("a::attr(href)").extract()

        # 给所有url拼接上主域名，如果没有主域名的话
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]

        # 可能包含javascript:;，过滤
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)

        url_pat = re.compile("(.*zhihu.com/question/(\d+))(/|$).*")

        # 在parse_question里也可以进行下面的操作，以继续进行跟踪，这里就不再跟踪下去了
        for url in all_urls:
            match_obj = url_pat.match(url)
            # 如果是question相关的的URL，则下载并交由提取函数进行字段的提取
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, meta={'question_id': question_id},
                                     headers=self.headers, callback=self.parse_question)
            # 否则的话进一步跟踪
            else:
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        """
        提取知乎问题相应字段
        """
        question_id = int(response.meta.get("question_id", ""))
        item_loader = ItemLoader(item=ZhihuQuestionItem, response=response)
        item_loader.add_css("title", ".QuestionHeader-content h1::text")
        item_loader.add_css("content", ".QuestionHeader-detail span::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("zhihu_id", question_id)
        item_loader.add_css("watcher_num", ".NumberBoard.QuestionFollowStatus-counts .NumberBoard-value::text")
        item_loader.add_css("answer_num", ".List-headerText span::text")
        item_loader.add_css("click_num", ".NumberBoard.QuestionFollowStatus-counts .NumberBoard-value::text")
        item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
        question_item = item_loader.load_item()

        # 传入问题的id，每次请求的数量，以及第一次请求的偏移值
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers,
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        """
        分析API返回的json格式文件，从中提取信息
        """
        answer_json = json.load(response.text)
        is_end = answer_json["paging"]["is_end"]
        next_url = answer_json["paging"]["next"]

        for answer in answer_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            # 用户可能匿名，此时就没有ID，所以这里要判断一下，是否有该字段
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.now()
            yield answer_item

        # 不是回答结尾的话继续通过next_url获得回答
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        """
        ZhihuSpider的入口,首先在这里进行请求，从登陆页面得到response，并调用login函数。
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
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "13419516267",
                "password": "ssjusher123",
                "captcha": ""
            }
            # 这里为了获得验证码图片，在发送一个取得验证码图片的请求，将登陆延迟到login_after_captcha函数中，scrapy的Requests会自动管理cookies
            # 当然也可以直接通过requests来发送相应请求来获得验证码图片，不过要设置cookies，从response里获得,确保cookies一致
            numbers = str(int(time.time()*1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(numbers)
            yield scrapy.Request(captcha_url, meta={"post_data": post_data}, headers=self.headers,
                                 callback=self.login_after_captcha)

    def login_after_captcha(self, response):
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = response.meta.get("post_data", {})
        with open("captcha.jpg", "wb") as f:
                f.write(response.body)

        try:
            # 显示验证码
            im = Image.open("captcha.jpg")
            im.show()
            im.close()
        except Exception as e:
            print(e)

        captcha = input("请手动输入验证码:")
        post_data["captcha"] = captcha
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

