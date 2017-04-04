# -*- coding: utf-8 -*-
from scrapy.http import Request
from urllib import parse
import scrapy

from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com"]
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        # 当前页的所有文章的url
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')

        # scrapy下载内容并进行解析
        for post_node in post_nodes:
            # 封面图url
            image_url = post_node.css('img::attr(src)').extract_first('')
            # 文章url
            post_url = post_node.css('::attr(href)').extract_first('')
            yield Request(url=parse.urljoin(response.url, post_url), meta={'front_image_url': image_url},
                          callback=self.parse_details)

        # 提取下一页url并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_details(self, response):
        """
        提取具体字段
        """
        # # 通过CSS选择器提取文章的具体字段，并添加到item中
        # title = response.css('.entry-header h1::text').extract_first()
        # create_date = response.css('.entry-meta-hide-on-mobile::text').extract_first().replace('·', '').strip()
        # # 数据库里定义的是date对象，所以这里要处理一下
        # try:
        #     create_date = self.pares_ymd(create_date)
        # except Exception as e:
        #     create_date = datetime.now().date()
        # tag = response.css('.entry-meta-hide-on-mobile a::text').extract()[-1]
        # front_image_url = response.meta.get("front_image_url", "")
        # content = response.css("div.entry").extract_first()
        # fav_nums = response.css(".bookmark-btn::text").extract()[0]
        # match_re = re.match(".*?(\d+).*", fav_nums)
        # if match_re:
        #     fav_nums = int(match_re.group(1))
        # else:
        #     fav_nums = 0
        #
        # # item对应字段填充值
        # article_item = JobBoleArticleItem()
        # article_item["title"] = title
        # article_item["url"] = response.url
        # article_item["create_date"] = create_date
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item["tag"] = tag
        # article_item["front_image_url"] = [front_image_url]
        # article_item["content"] = content
        # article_item["fav_nums"] = fav_nums
        # article_item["front_image_path"] = " "

        # 通过item loader加载item
        # 文章封面图
        front_image_url = response.meta.get("front_image_url", "")
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_css("create_date", ".entry-meta-hide-on-mobile::text")
        item_loader.add_css("tag", ".entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        article_item = item_loader.load_item()
        # 调用后传递到pipelines.py
        yield article_item


