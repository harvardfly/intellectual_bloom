# coding:utf-8

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options

from tornado.options import define, options
from app.settings import configs
from app.urls import urls

define("port", type=int, default=8007, help="运行端口")


class IntellectualApplication(tornado.web.Application):
    def __init__(self):
        super(IntellectualApplication, self).__init__(handlers=urls, **configs)  # NOQA


def create_http_server():
    # 运行程序在命令行中启动
    tornado.options.parse_command_line()
    # 创建http服务对象，传入实例化后自定义应用
    http_server = tornado.httpserver.HTTPServer(IntellectualApplication())
    # 服务绑定端口
    http_server.listen(options.port)
    # 启动输入输出事件循环
    tornado.ioloop.IOLoop.instance().start()
