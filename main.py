# -*- encoding: utf-8 -*-
from scrapy.cmdline import execute

import sys
import os

_author_ = 'shishengjia'
_date_ = '2017/3/26 18:59'

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy', 'crawl', 'jobbole'])
# execute(['scrapy', 'crawl', 'zhihu'])
# execute(['scrapy', 'crawl', 'lagou'])
# execute(['scrapy', 'crawl', 'RentInfo'])
