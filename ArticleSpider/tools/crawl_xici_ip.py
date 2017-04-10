# -*- coding: utf-8 -*-

import requests
import MySQLdb
from scrapy.selector import Selector


conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="ssjusher123", db="articlespider", charset="utf8")
cursor = conn.cursor()


def crawl_ip():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    }

    for i in range(1, 100):
        response = requests.get("http://www.xicidaili.com/nn/{0}".format(i), headers=headers)
        selector = Selector(text=response.text)

        ip_list = []

        all_trs = selector.xpath('//*[@id="ip_list"]/tr')
        for tr in all_trs[1:]:
            country = tr.xpath('td[1]/img/@alt').extract_first()
            ip_address = tr.xpath('td[2]/text()').extract_first()
            port = int(tr.xpath('td[3]/text()').extract_first())
            server_address = tr.xpath('td[4]/a/text()').extract_first()
            type = tr.xpath('td[6]/text()').extract_first()
            speed = float(tr.xpath('td[7]/div/@title').extract_first().strip('秒'))
            connect_time = float(tr.xpath('td[8]/div/@title').extract_first().strip('秒'))

            ip_list.append((country, ip_address, port, server_address, type, speed, connect_time))

        for item in ip_list:
            sql = """
                insert into ip_pool(country, ip_address, port, server_address, types, speed, connect_time) VALUES
                ('{0}', '{1}', {2}, '{3}', '{4}', {5}, {6}) ON DUPLICATE KEY UPDATE ip_address=VALUES(ip_address)
            """.format(item[0], item[1], item[2], item[3], item[4], item[5], item[6])

            cursor.execute(sql)
            conn.commit()