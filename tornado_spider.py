import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from tornado import gen, httpclient, ioloop, queues

base_url = "https://www.cnblogs.com/"
concurrency = 3


async def get_url_links(url):
    """
    获取url
    :param url:
    :return:
    """
    response = await httpclient.AsyncHTTPClient().fetch(url)
    html = response.body.decode("utf8")
    soup = BeautifulSoup(html)
    links = [
        urljoin(base_url, a.get("href"))
        for a in soup.find_all("a", href=True)
        if a.get("href").endswith(".html")
        ]
    return links


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
    seen_set = set()
    q = queues.Queue()

    async def fetch_url(current_url):
        # 得到一个url下的所有 urls 并放入tornado提供的队列中
        if current_url in seen_set:
            return

        seen_set.add(current_url)
        next_urls = await get_url_links(current_url)
        for new_url in next_urls:
            print(new_url)
            await get_info_data(new_url)
            if new_url.startswith(base_url):
                # 放入队列
                await q.put(new_url)

    async def worker():
        async for url in q:
            if url is None:
                return
            try:
                await fetch_url(url)
            except Exception as e:
                print("excepiton")
            finally:
                q.task_done()

    # 放入初始url到队列
    await q.put(base_url)

    # 启动协程
    workers = gen.multi([worker() for _ in range(concurrency)])
    await q.join()

    for _ in range(concurrency):
        await q.put(None)

    await workers


if __name__ == "__main__":
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
