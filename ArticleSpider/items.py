# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from datetime import datetime
import scrapy
import re

from ArticleSpider.settings import SQL_DATETIME_FORMAT

from ArticleSpider.utils.common import date_convert


def get_nums(value):
    """
    提取数字
    """
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


def return_value(value):
    """
    直接返回自身
    """
    return value


def remove_comment_tags(value):
    """
    tag可能包括评论这一元素，有的话则去除
    """
    if "评论" in value:
        return ""
    else:
        return value


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    # 配置默认的output_processor,取出list中的第一个元素
    default_output_processor = TakeFirst()


class QuestionItemLoader(ItemLoader):
    # 自定义知乎问题itemloader
    # 配置默认的output_processor,取出list中的第一个元素
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    """
    所有提取到的值都存储在列表里，待处理
    input_processor用来处理获取的内容，不指定则为默认值
    output_processor用来最后输出，不指定则为默认值
    MapCompose函数里可添加任意多函数，每个函数都会作用于列表里的每个元素，类似map函数
    """
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        # 下载图片的uel需要存储在list中，所以这里直接返回自身即可
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    tag = scrapy.Field(
        # 可能夹杂评论这一元素，将其去除
        input_processor=MapCompose(remove_comment_tags),
        # 将tag元素串联起来
        output_processor=Join(",")
    )
    content = scrapy.Field()
    fav_nums = scrapy.Field(
        # 类似于'1 赞'，从中提取数字
        input_processor=MapCompose(get_nums)
    )

    def get_insert_sql(self):
        """
        插入语句和参数
        """
        insert_sql = """
            insert into jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path,
            tag, content, fav_nums)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # 注意front_image_url在item是以list的形式，所以先要提取出来
        front_image_url = ""
        if self["front_image_url"]:
            front_image_url = self["front_image_url"][0]
        params = (self["title"], self["create_date"], self["url"], self["url_object_id"], front_image_url,
                  self["front_image_path"], self["tag"], self["content"], self["fav_nums"])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    # 知乎问题
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    conetnt = scrapy.Field()
    answer_num = scrapy.Field()
    watcher_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, watcher_num, click_num,
                crawl_time)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num),
                 watcher_num=VALUES(watcher_num), click_num=VALUES(click_num)
            """
        zhihu_id = "".join(self["zhihu_id"])
        topics = ",".join(self["topics"])
        url = "".join(self["url"])
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = get_nums("".join(self["answer_num"]))
        watcher_num = int(self["watcher_num"][0])
        click_num = int(self["click_num"][1])
        crawl_time = datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, watcher_num, click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎问题回答
    # 知乎问题的回答是通过api获取的，能直接获取到值，所以这里就不用itemloader了
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, praise_num, comments_num,
              create_time, update_time, crawl_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), praise_num=VALUES(praise_num),
              update_time=VALUES(update_time)
        """
        zhihu_id = self["zhihu_id"]
        url = self["url"]
        question_id = self["question_id"]
        author_id = self["author_id"]
        content = self["content"]
        praise_num = self["praise_num"]
        comments_num = self["comments_num"]
        create_time = datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        crawl_time = self["crawl_time"].strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, url, question_id, author_id, content, praise_num, comments_num, create_time, update_time,
                  crawl_time)

        return insert_sql, params
