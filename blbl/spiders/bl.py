# -*- coding: utf-8 -*-
import scrapy
from blbl.items import BlblItem
import json
def algorithm_dec(bv):
    Str = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'  # 准备的一串指定字符串
    Dict = {}  # 建立一个空字典

    # 将字符串的每一个字符放入字典一一对应 ， 如 f对应0 Z对应1 一次类推。
    for i in range(58):
        Dict[Str[i]] = i
    # print(tr) #如果你实在不理解请将前面的注释去掉，查看字典的构成

    s = [11, 10, 3, 8, 4, 6, 2, 9, 5, 7]  # 必要的解密列表
    xor = 177451812  # 必要的解密数字 通过知乎大佬的观察计算得出 网址：https://www.zhihu.com/question/381784377
    add = 100618342136696320  # 这串数字最后要被减去或加上
    if bv.find('BV') == -1:
        bv = 'BV' + bv

    r = 0
    # 下面的代码是将BV号的编码对照字典转化并进行相乘相加操作 **为乘方
    for i in range(10):
        r += Dict[bv[s[i]]] * 58 ** i
    av = str((r - add) ^ xor)
    return av
class BlSpider(scrapy.Spider):
    name = 'bl'
    allowed_domains = ['bilibili.com']

    start_urls = ['https://www.bilibili.com/v/popular/rank/all',
                 'https://www.bilibili.com/v/popular/rank/guochuang',
                 'https://www.bilibili.com/v/popular/rank/douga',
                 'https://www.bilibili.com/v/popular/rank/music',
                 'https://www.bilibili.com/v/popular/rank/dance',
                 'https://www.bilibili.com/v/popular/rank/game',
                 'https://www.bilibili.com/v/popular/rank/technology',
                 'https://www.bilibili.com/v/popular/rank/digital',
                 'https://www.bilibili.com/v/popular/rank/life',
                 'https://www.bilibili.com/v/popular/rank/food'
                  ]



    def parse(self, response):
        rank_tab=response.xpath('//ul[@class="rank-tab"]/li[@class="rank-tab--active"]/text()').getall()
        print('='*50,'当前爬取榜单为:',rank_tab,'='*50)

        #视频的信息都放在li标签中，这里先获取所有的li标签
        #之后遍历rank_lists获取每个视频的信息
        rank_lists=response.xpath('//ul[@class="rank-list"]/li')
        for rank_list in rank_lists:
            #id = rank_list.xpath("@data-id")
            rank_num=rank_list.xpath('div[@class="num"]/text()').get()
            title=rank_list.xpath('div/div[@class="info"]/a/text()').get()
            # 抓取视频的url，切片后获得视频的id
            bid=rank_list.xpath('div/div[@class="info"]/a/@href').get().split('/BV')[-1]
            id = algorithm_dec('BV'+bid)
            # 拼接详情页api的url
            Detail_link=f'https://api.bilibili.com/x/web-interface/archive/stat?aid={id}'
            Labels_link=f'https://api.bilibili.com/x/tag/archive/tags?aid={id}'
            author=rank_list.xpath('div/div[@class="info"]/div[@class="detail"]/a/span/text()').get()
            score=rank_list.xpath('div/div[@class="info"]/div[@class="pts"]/div/text()').get()

            items={
                'rank_tab':rank_tab,
                'rank_num' : rank_num ,
                'title' :title ,
                'id' : id ,
                'author' : author ,
                'score' : score ,
                'Detail_link':Detail_link
            }
            print(items)
            # 将api发送给调度器进行详情页的请求，通过meta传递排行页数据
            yield scrapy.Request(url=Labels_link,callback=self.Get_labels,meta={'item':items},dont_filter=True)

    def Get_labels(self,response):
        items=response.meta['item']
        Detail_link=items['Detail_link']
        # 解析json数据
        html=json.loads(response.body)
        Tags=html['data'] #视频标签数据
        tag_name=','.join([i['tag_name'] for i in Tags])
        items['tag_name']=tag_name
        yield scrapy.Request(url=Detail_link,callback=self.Get_detail,meta={'item':items},dont_filter=True)

    def Get_detail(self,response):
        # 获取排行页数据
        items=response.meta['item']
        rank_tab=items['rank_tab']
        rank_num=items['rank_num']
        title=items['title']
        id=items['id']
        author=items['author']
        score=items['score']
        tag_name=items['tag_name']

        # 解析json数据
        html=json.loads(response.body)

        # 获取详细播放信息
        stat=html['data']

        view=stat['view']
        danmaku =stat['danmaku']
        reply =stat['reply']
        favorite =stat['favorite']
        coin =stat['coin']
        share =stat['share']
        like =stat['like']

        item=BlblItem(
            rank_tab=rank_tab,
            rank_num = rank_num ,
            title = title ,
            id = id ,
            author = author ,
            score = score ,
            view = view ,
            danmaku = danmaku ,
            reply = reply ,
            favorite = favorite ,
            coin = coin ,
            share = share ,
            like = like ,
            tag_name = tag_name
        )
        yield item
