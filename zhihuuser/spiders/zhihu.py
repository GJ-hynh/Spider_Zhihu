# -*- coding: utf-8 -*-
from scrapy import Spider, Request
import json
from zhihuuser.items import UserItem


class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_uris = ['http://www.zhihu.com/']

    start_user = 'excited-vczh'

    user_uri = "http://www.zhihu.com/api/v4/members/{user}?include={include}"
    user_query = "allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics"

    follows_uri = "https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}"
    follows_query = "data[*].answer_count, articles_count, gender, follower_count, is_followed, is_following, badge[?(type=best_answerer)].topics"

    followers_uri = "https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}"
    followers_query = "data[*].answer_count, articles_count, gender, follower_count, is_followed, is_following, badge[?(type=best_answerer)].topics"

    def start_requests(self):
        # 请求自己本身信息，请求关注列表，请求粉丝列表
        yield Request(self.user_uri.format(user=self.start_user, include=self.user_query), self.parse_user)
        yield Request(self.follows_uri.format(user=self.start_user, include=self.follows_query, offset=0, limit=20), callback=self.parse_follows)
        yield Request(self.followers_uri.format(user=self.start_user, include=self.followers_query, offset=0, limit=20), callback=self.parse_followers)

    def parse_user(self, response):
        # 解析item信息
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item

        #分别获取user的关注列表和粉丝列表，进行下一步递归调用
        yield Request(self.follows_uri.format(user=result.get('url_token'), include=self.follows_query, limit=20, offset=0), self.parse_follows)
        yield Request(self.followers_uri.format(user=result.get('url_token'), include=self.followers_query, limit=20, offset=0), self.parse_followers)


    def parse_follows(self, response):
        # 既要获得关注列表的每个人的信息，重新请求parse_user。又要进行分页操作
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_uri.format(user=result.get('url_token'), include=self.user_query), self.parse_user)

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_follows)

    def parse_followers(self, response):
        # 既要获得关注列表的每个人的信息，重新请求parse_user。又要进行分页操作
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_uri.format(user=result.get('url_token'), include=self.user_query), self.parse_user)

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_followers)




