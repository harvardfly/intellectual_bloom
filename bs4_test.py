import re
import requests

from bs4 import BeautifulSoup

# 博客园
# html = requests.get("https://www.cnblogs.com/yilezhu/p/9926078.html").content
# html1 = requests.get("http://www.cnblogs.com/mvc/blog/news.aspx?blogApp=yilezhu").content
# soup = BeautifulSoup(html)
# title = soup.find(id="cb_post_title_url").get_text()
# print(title)
# info = soup.find(id="cnblogs_post_body")
# # print(info)
# soup1 = BeautifulSoup(html1)
# author = soup1.select('div > a')
# print([author[i].get_text() for i in range(0, 4)])  # 昵称 园龄 粉丝 关注
# base_url = 'https://news.cnblogs.com/'
# response = requests.get('https://news.cnblogs.com/')
# response.encoding = response.apparent_encoding
# from urllib.parse import urljoin
#
# soup = BeautifulSoup(response.text)
# newslist = soup.find_all('div', class_="content")
# newslist = [urljoin(base_url, shot_url.a.get("href")) for shot_url in newslist]
#
# print(newslist)


# CSDN
# base_url = 'http://blog.csdn.net'
# response = requests.get('https://blog.csdn.net/nav/news')
# response.encoding = response.apparent_encoding
# from urllib.parse import urljoin
#
# soup = BeautifulSoup(response.content)
# newslist = soup.find_all('div', class_="list_con")
# newslist = [urljoin(base_url, shot_url.a.get("href")) for shot_url in newslist]
#
# for url in newslist:
#     response_info = requests.get(url)
#     response_info.encoding = response_info.apparent_encoding
#     soup_info = BeautifulSoup(response_info.content)
#     title = soup_info.find(class_="title-article").get_text()
#     content = soup_info.find(id="article_content")
#     author_name = soup_info.find(id="uid")
#     print(author_name.text)  # 昵称


# https://www.jianshu.com/
base_url = 'https://www.jianshu.com/c/V2CqjW'
response = requests.get(base_url)
response.encoding = response.apparent_encoding
from urllib.parse import urljoin

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
}
page = requests.get(base_url, headers=headers)
soup = BeautifulSoup(page.content)
print(soup)
newslist = [url.get("href") for url in soup.find_all("a", href=True)]
# newslist = [urljoin(base_url, shot_url.a.get("href")) for shot_url in newslist]
print(newslist)
# for url in newslist:
#     response_info = requests.get(url)
#     response_info.encoding = response_info.apparent_encoding
#     soup_info = BeautifulSoup(response_info.content)
#     title = soup_info.find(class_="title-article").get_text()
#     content = soup_info.find(id="article_content")
#     author_name = soup_info.find(id="uid")
#     print(author_name.text)  # 昵称


# url = "http://www.jianshu.com"
#
# # page_info = requests.urlopen(page).read().decode('utf-8')  # 打开Url,获取HttpResponse返回对象并读取其ResposneBody
#
# # 将获取到的内容转换成BeautifulSoup格式，并将html.parser作为解析器
# soup = BeautifulSoup(page.content)
# # 以格式化的形式打印html
# # print(soup.prettify())
#
# titles = soup.find_all('a', 'title')  # 查找所有a标签中class='title'的语句
# print(titles)
