#!/usr/bin/env python
# coding=utf-8

import os
import re
import random
import time
from datetime import datetime
from datetime import date
from itertools import cycle
from bs4 import BeautifulSoup

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import make_aware

from douban_group_spy.const import USER_AGENT, DATETIME_FORMAT, DATE_FORMAT

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'douban_group_spy.settings')
import django
django.setup()

import click
import requests
import logging

from douban_group_spy.settings import GROUP_TOPICS_BASE_URL, GROUP_INFO_BASE_URL, DOUBAN_BASE_HOST, COOKIE
from douban_group_spy.models import Group, Post


lg = logging.getLogger(__name__)
# douban_base_host = cycle(DOUBAN_BASE_HOST)


def process_posts(posts, group, keywords, exclude):
    for t in posts:
        # ignore title or content including exclude keywords
        exclude_flag = False
        for e in exclude:
            if e in t['title'] or e in t['content']:
                exclude_flag = True
                break
        if exclude_flag:
            continue

        post = Post.objects.filter(post_id=t['id']).first()
        # ignore same id
        if post:
            lg.info(f'[post] update existing post: {post.post_id}')
            post.updated = make_aware(datetime.strptime(t['updated'], DATETIME_FORMAT))
            post.title = t['title']
            post.save(force_update=['updated', 'title'])
            continue
        # ignore same title
        if Post.objects.filter(title=t['title']).exists():
            lg.info(f'[post] ignore same title...')
            continue

        keyword_list = []
        is_matched = False
        for k in keywords:
            k_pattern = '.?'.join([i for i in k])
            if re.search(k_pattern, t['title']) or re.search(k_pattern, t['content']):
                keyword_list.append(k)
                is_matched = True

        post = Post(
            post_id=t['id'], group=group,
            author_info=t['author'], alt=t['alt'],
            title=t['title'], content=t['content'],
            photo_list=t['photos'],
            # rent=0.0, subway='', contact='',
            is_matched=is_matched, keyword_list=keyword_list,
            created=make_aware(datetime.strptime(t['created'], DATETIME_FORMAT)),
            updated=make_aware(datetime.strptime(t['updated'], DATETIME_FORMAT))
        )
        post.save(force_insert=True)
        lg.info(f'[post] save post: {post.post_id}')


def crawl(group_id, pages, keywords, exclude):
    lg.info(f'start crawling group: {group_id}')
    try:
        group = Group.objects.get(id=group_id)
    except ObjectDoesNotExist:
        lg.info(GROUP_INFO_BASE_URL.format(DOUBAN_BASE_HOST, group_id))
        html = requests.get(GROUP_INFO_BASE_URL.format(DOUBAN_BASE_HOST, group_id), headers={'User-Agent': USER_AGENT, 'Cookie': COOKIE}).text
        g_info = BeautifulSoup(html,'lxml')
        lg.info(f'Getting group: {group_id} successful')
        member_count_text=g_info.select_one(f"a[href='https://www.douban.com/group/{group_id}/members']").get_text()
        created_text=g_info.select_one('.group-loc').get_text()
        group = Group(
            id=group_id,
            name=g_info.select_one('h1').get_text().strip(),
            alt=f'https://www.douban.com/group/{group_id}',
            member_count=int(re.findall(r'[(](.*?)[)]', member_count_text)[0]),
            created=make_aware(datetime.strptime(re.findall(r"创建于(.+?) ",created_text)[0], DATE_FORMAT))
        )
        group.save(force_insert=True)

    for p in range(pages):
        time.sleep(random.randint(5,8))
        # host = next(douban_base_host)
        kwargs = {
            'url': GROUP_TOPICS_BASE_URL.format(DOUBAN_BASE_HOST, group_id),
            'params': {'start': p*25},
            'headers': {'User-Agent': USER_AGENT,'Cookie': COOKIE}
        }
        req = getattr(requests, 'get')(**kwargs)
        lg.info(f'getting: {req.url}, status: {req.status_code}')
        # if 400, switch host
        if req.status_code != 200:
            # host = next(douban_base_host)
            kwargs['url'] = GROUP_TOPICS_BASE_URL.format(DOUBAN_BASE_HOST, group_id)
            lg.info(f'Rate limit, switching host')
            req = getattr(requests, 'get')(**kwargs)
            lg.info(f'getting group: {req.url}, status: {req.status_code}')
            if req.status_code != 200:
                lg.warning(f'Fail to getting: {req.url}, status: {req.status_code}')
                continue

        soup = BeautifulSoup(req.text,'lxml')
        posts=[]
        for row in soup.select('table[class="olt"] tr[class=""]'):
            time.sleep(random.randint(3,5))
            link=row.select_one('td[class="title"] a')
            link_href=link["href"]
            post_detail_html = requests.get(link_href, headers={'User-Agent': USER_AGENT, 'Cookie': COOKIE}).text
            post_detail = BeautifulSoup(post_detail_html,'lxml')
            post_content=post_detail.select_one('div[class="topic-content"]')
            post_photos=[]
            for photo_row in post_content.select('img'):
                post_photos.append(photo_row['src'])

            result={}
            result['id']=int(re.findall(r"https://www.douban.com/group/topic/(.+?)/",link_href)[0])
            result['title']=link["title"]
            result['content']=post_content.get_text().strip()
            result['alt']=link_href
            author_link=row.select("td")[1].select_one('a')
            result['author']={'name':author_link.get_text(),'alt':author_link["href"]}
            result['photos']=post_photos
            result['created']=post_detail.select_one('.create-time').get_text()
            result['updated']=f'{date.today().year}-{row.select("td")[3].get_text()}:00'
            posts.append(result)
        process_posts(posts, group, keywords, exclude)
    

@click.command(help='example: python crawler_main.py -g 10086 -g 12345 -k xx花园 -k xx地铁 -e 求租')
@click.option('--groups', '-g', help='group id', required=True, multiple=True, type=str)
@click.option('--keywords', '-k',  help='search keywords', multiple=True, type=str)
@click.option('--exclude', '-e',  help='excluded keywords', multiple=True, type=str)
@click.option('--sleep', help='time sleep', default=60 * 15)
@click.option('--pages', help='crawl page range', default=10)
@click.option('-v', help='Show debug info', is_flag=True)
def main(groups: tuple, keywords: tuple, exclude: tuple, sleep, pages, v):
    if v:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    while True:
        for g_id in groups:
            crawl(g_id, pages, keywords, exclude)
        lg.info('Sleeping...')
        time.sleep(sleep)


if __name__ == '__main__':
    main()
