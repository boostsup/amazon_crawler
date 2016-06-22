# -*- coding: 'utf-8' -*-

import urllib, urllib2, re, time, StringIO, gzip
from multiprocessing import Pool, Queue, Manager
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from lxml import etree
import sys, os
#set default decoding way,when encoding
reload(sys)
sys.setdefaultencoding('utf-8')

#iask class
class AmazonSpider:
    '''
    this the base crawler
    '''
    #initial
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        #initial headers
        self.headers = {'User-Agent': self.user_agent}
        #accept encode
        self.headers['Accept-Encoding'] = 'gzip, deflate'
        #url
        self.url = 'https://www.amazon.com/Volcom-Mens-Hybrid-Short-Dark/dp/B013V1OHFS/ref=lp_14146712011_1_3?s=apparel&ie=UTF8&qid=1466392801&sr=1-3&nodeID=14146712011'
        #data
        self.data = []
        #driver
        self.driver = webdriver.Chrome()
    
    def getPageSource(self, url):
        '''
        func get the html code of the url(urilib2)
        '''
        try:
            #make a request
            request = urllib2.Request(url, headers = self.headers)
            #get a response
            response = urllib2.urlopen(request)
            #gzip,add this code
            if response.info().get('Content-Encoding', '') == 'gzip':
                    buf = StringIO.StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    pageCode = f.read().decode('utf-8')
            else:
                #pageCode
                pageCode = response.read().decode('utf-8')
        except urllib2.URLError,e:
            print e.reason
        if pageCode:
            print 'Process %s: PageCode Get Success...'%os.getpid()
            return pageCode
        else:
            print 'Process %s: ageCode Get False...'%os.getpid()
            return None

    def checkContent(self, content):
        if content:
            return content
        else:
            return 'noexit'


    def getHTML(self, url):
        '''
        func use selenium
        '''
        self.driver.get(url)
        return self.driver.page_source

    def parseBase(self, html):
        '''
        func to parse content
        '''
        self.selBase = etree.HTML(html)
        self.name = self.checkContent(self.driver.find_element_by_xpath("//span[@id='productTitle']").text)
        self.intro = self.checkContent(self.driver.find_element_by_xpath("//div[@id='feature-bullets']").text)
        self.color_list = self.selBase.xpath("//div[@id='variation_color_name']//li/@id")
        self.size_list = self.selBase.xpath("//select[@id='native_dropdown_selected_size_name']//option/@id")

    def parseOther(self, size):
        '''
        func parse the other element
        '''
        self.selOther = etree.HTML(self.driver.page_source)
        try:    
            self.price = self.checkContent(self.driver.find_element_by_xpath("//span[@id='priceblock_ourprice']").text)
        except:
            try:
                self.price = self.checkContent(self.driver.find_element_by_xpath("//span[@id='priceblock_saleprice']").text)
            except:
                self.price = '/'
        self.size = self.checkContent(self.driver.find_element_by_xpath("//option[@id='"+size+"']").text)
        self.color = self.checkContent(self.driver.find_element_by_xpath("//div[@id='variation_color_name']//span").text)
        self.image_url = self.checkContent(self.selOther.xpath("//div[@id='altImages']//img/@src"))

def start(color_id, size_list, url, q):
    '''
    start
    '''
    print 'Process %s start.'%os.getpid()
    thread = AmazonSpider()
    thread.driver.get(url)
    time.sleep(5)
    xpath = "//li[@id='"+color_id+"']"
    thread.driver.find_element_by_xpath(xpath).click()
    time.sleep(3)
    for size in size_list:
        if size == 'native_size_name_-1':
            continue
        if 'U' in thread.driver.find_element_by_xpath("//option[@id='"+size+"']").get_attribute('class'):
            continue
        else:
            thread.driver.find_element_by_xpath("//option[@id='"+size+"']").click()
            time.sleep(3)
            thread.parseOther(size)
        q.put([thread.color, thread.price, thread.size, thread.image_url])
    print 'Process %s end.'%os.getpid()
    thread.driver.quit()

if __name__ == '__main__':
    '''
    main ,start here
    '''
    now = time.time()
    amazon = AmazonSpider()
    html = amazon.getHTML(amazon.url)
    time.sleep(5)
    amazon.parseBase(html)
    pool = Pool(5)
    q = Manager().Queue()
    for color_id in amazon.color_list:
        pool.apply_async(start, args = (color_id, amazon.size_list, amazon.url, q, ))
    pool.close()
    pool.join()
    while q.qsize() != 0:
        print q.get(False)
    end = time.time()
    print (end-now)
    amazon.driver.quit()
    # for color_id in amazon.color_list:
    #     xpath = "//li[@id='"+color_id+"']"
    #     amazon.driver.find_element_by_xpath(xpath).click()
    #     time.sleep(2)
    #     for size in amazon.size_list:
    #         if size == 'native_size_name_-1':
    #             continue
    #         if 'U' in amazon.driver.find_element_by_xpath("//option[@id='"+size+"']").get_attribute('class'):
    #             continue
    #         else:
    #             amazon.driver.find_element_by_xpath("//option[@id='"+size+"']").click()
    #             time.sleep(2)
    #             amazon.parseOther(size)
    #         amazon.data.append([amazon.name, amazon.color, amazon.price, amazon.size, amazon.image_url, amazon.intro])
    #         print amazon.name, amazon.color, amazon.price, amazon.size, amazon.image_url, amazon.intro
    # end = time.time()
    # for data in amazon.data:
    #     print data
    # print 'end'
    # print (end - now)
