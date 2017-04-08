# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime

from items import LagouJobItemLoader, LagouJobItem
from utils.common import get_md5


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    # 制定匹配规则
    # 在匹配到页面的url符合前两个规则的时候，继续follow此页面符合第三条规则的链接，并调用parse_job函数进行处理，当然在此页面继续follow
    rules = (
        Rule(LinkExtractor(allow=(r'zhaopin/.*', )), follow=True),
        Rule(LinkExtractor(allow=(r'gongsi/j\d+.html', )), follow=True),
        Rule(LinkExtractor(allow=r'/jobs/\d+.html'), callback='parse_job', follow=True),
    )

    # 这两个函数可以加入自定义的处理内容,
    # def parse_start_url(self, response):
    #     return []
    #
    # def process_results(self, response, results):
    #     return results

    def parse_job(self, response):
        """
        解析职位信息页面
        """
        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", '.job-name::attr(title)')
        # 这里最小最大薪资和最短最长工作年限等到item里再去处理
        item_loader.add_css("salary", '.job_request .salary::text')
        item_loader.add_xpath("job_city", '//*[@class="job_request"]/p/span[2]/text()')
        item_loader.add_xpath("work_years", '//*[@class="job_request"]/p/span[3]/text()')
        item_loader.add_xpath("degree_need", '//*[@class="job_request"]/p/span[4]/text()')
        item_loader.add_xpath("job_type", '//*[@class="job_request"]/p/span[5]/text()')
        item_loader.add_css("tags", '.position-label li::text')
        item_loader.add_css("publish_time", '.publish_time::text')
        item_loader.add_css("job_advantage", '.job-advantage p::text')
        item_loader.add_css("job_desc", '.job_bt div')
        # 地点的提取处理放在item里完成。
        item_loader.add_css("job_address", '.work_addr')
        item_loader.add_css("company_name", '.job_company dt a img::attr(alt)')
        item_loader.add_css("company_url", '.job_company dt a::attr(href)')
        item_loader.add_value("crawl_time", datetime.now())
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("url", response.url)

        job_item = item_loader.load_item()

        return job_item
