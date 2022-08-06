# 豆瓣小组爬虫

## 2021.07.19 Update: 感谢 [xwjdsh](https://github.com/xwjdsh) 的 [PR](https://github.com/lesywix/douban_group_spy/pull/11)，项目复活了

## ~~Update：豆瓣的接口废了~~

通过调用豆瓣接口，聚合想要爬取小组的租房信息，并可通过关键词进行匹配及排除。

为了方便，使用了 Django admin 进行数据的可视化。通过 Django admin 可对数据进行搜索，过滤等简单功能。

由于豆瓣的限制，爬取每篇帖子都会随机等待 3~5 秒，以尽量不触及 Rate Limit，爬取速度比较慢，但能获取更多内容。

## 环境
- python >= 3.6
- sqlite

## 使用
1. 创建 venv `python3 -m venv venv`, 并激活 `. venv/bin/activate`
2. 安装依赖 `pip install -r requirements.txt`
3. 数据库初始化 `make migrate`
4. 修改配置，由于豆瓣的限制，你需要设置 Cookie 后才能开始爬取。在网页上登录豆瓣，将 `douban_group_spy/settings.py` 中的 `COOKIE` 配置修改为你的 Cookie (cookie key 为 `dbcl2`)
5. 运行爬虫 eg: `python crawler_main.py -g 106955 -g baoanzufang -k 灵芝 -k 翻身 -e 求租`
6. 运行网页 `make run_server`, 默认账号密码均为 admin

### 爬虫参数
- `-g`: 要爬取小组的 id
- `-k`: 查找关键词
- `-e`: 排除关键词
- `--sleep`: 爬一个周期后暂停的时间, 默认 `60 * 30` 秒(15 分钟)
- `--pages`: 爬一个周期每个小组的页数，默认 `10` 页
- `-v`: 展示 debug 信息，默认 False

一个周期就是爬取参数里的所有小组，每个小组默认的爬取页数的总和。

## ps

### 推荐小组：
- 106955: 深圳租房团
- baoanzufang: 深圳宝安租房
- 498004：深圳南山租房团
- 551176: 深圳租房
- szsh: 深圳租房
- SZhouse: 深圳租房

### Screenshots
文章列表

![](https://github.com/weixianglin/douban_group_spy/raw/master/img/screenshots1.png)

文章详情

![](https://github.com/weixianglin/douban_group_spy/raw/master/img/screenshots2.png)

小组列表

![](https://github.com/weixianglin/douban_group_spy/raw/master/img/screenshots3.png)

小组详情

![](https://github.com/weixianglin/douban_group_spy/raw/master/img/screenshots4.png)
