#!/usr/bin/env python
# coding=utf-8

import os
import re
import time
from datetime import datetime
from itertools import cycle

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import make_aware

from douban_group_spy.const import USER_AGENT, DATETIME_FORMAT

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'douban_group_spy.settings')
import django
django.setup()

import click
import requests
import logging

from douban_group_spy.settings import GROUP_TOPICS_BASE_URL, GROUP_INFO_BASE_URL, DOUBAN_BASE_HOST
from douban_group_spy.models import Group, Post


lg = logging.getLogger(__name__)
douban_base_host = cycle(DOUBAN_BASE_HOST)


def process_posts(posts, group, keywords, exclude):
    for t in posts['topics']:
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
            photo_list=[i['alt'] for i in t['photos']],
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
        g_info = requests.get(GROUP_INFO_BASE_URL.format(DOUBAN_BASE_HOST[1], group_id)).json()
        lg.info(f'Getting group: {group_id} successful')
        group = Group(
            id=g_info['uid'],
            name=g_info['name'],
            alt=g_info['alt'],
            member_count=g_info['member_count'],
            created=make_aware(datetime.strptime(g_info['created'], DATETIME_FORMAT))
        )
        group.save(force_insert=True)

    for p in range(pages):
        time.sleep(8)
        host = next(douban_base_host)
        kwargs = {
            'url': GROUP_TOPICS_BASE_URL.format(host, group_id),
            'params': {'start': p},
            'headers': {'User-Agent': USER_AGENT}
        }
        req = getattr(requests, 'get')(**kwargs)
        lg.info(f'getting: {req.url}, status: {req.status_code}')
        # if 400, switch host
        if req.status_code != 200:
            host = next(douban_base_host)
            kwargs['url'] = GROUP_TOPICS_BASE_URL.format(host, group_id)
            lg.info(f'Rate limit, switching host')
            req = getattr(requests, 'get')(**kwargs)
            lg.info(f'getting group: {req.url}, status: {req.status_code}')
            if req.status_code != 200:
                lg.warning(f'Fail to getting: {req.url}, status: {req.status_code}')
                continue

        posts = req.json()
        process_posts(posts, group, keywords, exclude)


@click.command(help='example: python crawler_main.py -g 10086 -g 12345 -k xx花园 -k xx地铁 -e 求租')
@click.option('--groups', '-g', help='group id', required=True, multiple=True, type=str)
@click.option('--keywords', '-k',  help='search keywords', multiple=True, type=str)
@click.option('--exclude', '-e',  help='excluded keywords', multiple=True, type=str)
@click.option('--sleep', help='time sleep', default=60 * 30)
@click.option('--pages', help='crawl page range', default=20)
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
