#!/usr/bin/env python3

import time
from datetime import timedelta

from html.parser import HTMLParser
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup
from tornado import gen, httpclient, ioloop, queues

base_url = 'https://www.cnblogs.com/'
concurrency = 10


async def get_links_from_url(url):
    """Download the page at `url` and parse it for links.

    Returned links have had the fragment after `#` removed, and have been made
    absolute so, e.g. the URL 'gen.html#tornado.gen.coroutine' becomes
    'http://www.tornadoweb.org/en/stable/gen.html'.
    """
    response = await httpclient.AsyncHTTPClient().fetch(url)
    print('fetched %s' % url)

    html = response.body.decode("utf8", errors='ignore')
    soup = BeautifulSoup(html)
    return [urljoin(url, remove_fragment(a.get("href")))
            for a in soup.find_all("a", href=True)]


def remove_fragment(url):
    pure_url, frag = urldefrag(url)
    return pure_url


async def get_info_data(url):
    response = await httpclient.AsyncHTTPClient().fetch(url)
    html = response.body.decode("utf8")
    soup = BeautifulSoup(html)
    title = soup.find(id="cb_post_title_url").get_text()
    print(title)
    info = soup.find(id="cnblogs_post_body")
    name = url.split("/")[3]
    article_code = url.split("/")[-1].split(".")[0]
    print(article_code)
    print(name)
    author_url = "http://www.cnblogs.com/mvc/blog/news.aspx?blogApp={}".format(name)
    author_response = await httpclient.AsyncHTTPClient().fetch(author_url)
    author_html = author_response.body.decode("utf8")
    author_soup = BeautifulSoup(author_html)
    author = author_soup.select('div > a')
    print([author[i].get_text() for i in range(0, 4)])  # 昵称 园龄 粉丝 关注


async def main():
    q = queues.Queue()
    start = time.time()
    fetching, fetched = set(), set()

    async def fetch_url(current_url):
        if current_url in fetching:
            return

        print('fetching %s' % current_url)
        fetching.add(current_url)
        urls = await get_links_from_url(current_url)
        fetched.add(current_url)

        for new_url in urls:
            # Only follow links beneath the base URL
            if new_url.startswith(base_url) and new_url.endswith(".html"):
                await get_info_data(new_url)
                await q.put(new_url)

    async def worker():
        async for url in q:
            if url is None:
                return
            try:
                await fetch_url(url)
            except Exception as e:
                print('Exception: %s %s' % (e, url))
            finally:
                q.task_done()

    await q.put(base_url)

    # Start workers, then wait for the work queue to be empty.
    workers = gen.multi([worker() for _ in range(concurrency)])
    await q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    print('Done in %d seconds, fetched %s URLs.' % (
        time.time() - start, len(fetched)))

    # Signal all the workers to exit.
    for _ in range(concurrency):
        await q.put(None)
    await workers


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
