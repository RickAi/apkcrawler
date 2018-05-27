# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
import re
import urllib.request
import time
import sys
import os

class XiaomiSpider(scrapy.Spider):
    name = 'xiaomi'
    allowed_domains = ['app.mi.com']
    start_urls = ['http://app.mi.com/topList']

    base_url = "http://app.mi.com"
    base_dir = "./apkcrawler/apks/"
    max_apk_size = 1024 * 1024 * 100 # 100MB
    index = 0

    def start_requests(self):
        for page in range(1, 5):
            url = "http://app.mi.com/topList?page=" + str(page)
            yield Request(url)

    def parse(self, response):
        list_xpath = "/html/body/div[4]/div/div[1]/div[1]/ul/li/h5/a/@href"
        url_list = response.selector.xpath(list_xpath).extract()

        for url in url_list:
            info_url = self.base_url + url
            print("found a app item:" + info_url)
            yield Request(info_url, callback=self.parse_download_url)


    def parse_download_url(self, response):
        apk_name = re.search("\?id=(.*)", response.url).group(1)
        url = response.css("div[class=app-info-down] a::attr(href)").extract_first()
        download_url = self.base_url + url
        self.download(download_url, apk_name)

    # 下载应用
    def download(self, url, file_name):
        # 不下载大型app，当前主要为了避免游戏类应用
        result = urllib.request.urlopen(url)
        file_size = result.info()['Content-Length']
        if int(file_size) > self.max_apk_size:
            print("abandon large apk file:" + file_name)
            return

        self.index += 1
        file_path = self.base_dir + str(self.index) +  file_name + ".apk"

        opener = urllib.request.build_opener()
        opener.addheaders = [
            ("User-Agent",
             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36")
        ]

        print("start download:" + file_name + " with url:" + url)
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, file_path, reporthook=self.report_hook)

        self.install_apk(file_path)

    # 下载进展
    def report_hook(self, count, block_size, total_size):
        global start_time
        if count == 0:
            start_time = time.time()
            return

        duration = time.time() - start_time
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = min(int(count * block_size * 100 / total_size), 100)
        sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                         (percent, progress_size / (1024 * 1024), speed, duration))
        sys.stdout.flush()

    # 安装应用
    def install_apk(self, file_path):
        print("start install:" + file_path)
        os.system("adb install " + file_path)
