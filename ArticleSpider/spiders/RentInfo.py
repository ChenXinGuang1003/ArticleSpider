# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from items import RentInfoItem
from urllib import parse


class RentinfoSpider(scrapy.Spider):
    """
    爬取寄托论坛的租房信息
    """
    name = "RentInfo"
    allowed_domains = ["bbs.gter.net"]
    start_urls = ['http://bbs.gter.net/forum-1033-1.html']

    def parse(self, response):
        nodes = response.css('#moderate table tbody')

        for node in nodes:
            node_id = node.css('::attr(id)').extract_first("")
            if node_id.startswith("normalthread"):
                item = RentInfoItem()
                item["title"] = node.css('tr th a.xst::text').extract_first()
                item["url"] = node.css('tr th a.xst::attr(href)').extract_first()
                item["publish_date"] = node.xpath('tr/td[2]/em/span/text()').extract_first()
                yield item

        next_url = response.css('.nxt::attr(href)').extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse, dont_filter=True)
