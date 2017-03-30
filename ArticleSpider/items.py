# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
import scrapy
import re

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

