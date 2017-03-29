# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
"""
执行的顺序按照settings文件中的ITEM_PIPELINES中配置的优先值
"""
import codecs
import json
import MySQLdb
import MySQLdb.cursors

from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi


class JsonWithEncodingPipeline(object):
    """
    将爬取得内容以json格式进行保存
    """
    def __init__(self):
        self.file = codecs.open("article.json", "w", encoding="utf-8")

    def process_item(self, item, spider):
        """
        处理item，将内容保存，并返回item，以供下一个pipeline使用
        """
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spidr_closed(self):
        """
        在spider关闭的时候自动调用，关闭文件
        """
        self.file.close()


class ArticleImagesPipeline(ImagesPipeline):
    """
    继承ImagesPipeline，重写item_completed方法
    """
    def item_completed(self, results, item, info):
        for ok, value in results:
            image_file_path = value["path"]
        # 下载完成后记录图片存储路径
        item["front_image_path"] = image_file_path
        # 按照优先值，给pipeline执行完后将执行ArticlespiderPipeline，返回一个item
        return item


class MySQLPipeline(object):
    """
    将爬取的内容保存到数据库
    这里需要注意的是item["front_image_path"]是在ArticleImagesPipeline中被赋值，所以在settings文件中ArticleImagesPipeline
    的优先值应该大于MySQLPipeline
    另外，这是同步插入，在后期会出现插入速度跟不上爬取内容的速度，造成堵塞
    """
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', 'ssjusher123', 'articlespider', charset="utf8mb4", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path,
            tag, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        # 注意front_image_url在保存到item时是以list的形式，所以想要提取出来
        front_image_url = item["front_image_url"][0]
        self.cursor.execute(insert_sql, (item["title"], item["create_date"], item["url"], item["url_object_id"],
                                         front_image_url, item["front_image_path"], item["tag"], item["content"]))
        self.conn.commit()


class MySQLTwistedPipeline(object):
    """
    使用Twisted将MySQL插入数据变为异步执行
    """
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        """
        配置数据库连接
        """
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8mb4',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        # 处理异常
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print (failure)

    def do_insert(self, cursor, item):
        """
        插入逻辑
        """
        insert_sql = """
            insert into jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path,
            tag, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        # 注意front_image_url在保存到item时是以list的形式，所以想要提取出来
        front_image_url = item["front_image_url"][0]
        cursor.execute(insert_sql, (item["title"], item["create_date"], item["url"], item["url_object_id"],
                                    front_image_url, item["front_image_path"], item["tag"], item["content"]))
