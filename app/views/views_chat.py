# coding:utf-8

import json
import time
import tornado.web
from app.tools.orm import ORM
from app.models.models import Message
from sockjs.tornado import SockJSConnection


class ChatRoomHandler(SockJSConnection):
    pools = set()  # 定义连接池

    # 1.建立连接
    def on_con(self, request):
        # 连接加入到连接池
        self.pools.add(self)

    # 2.双向数据通信
    def on_message(self, message):
        try:
            # 处理消息，json格式，客户端设置
            data = json.loads(message)
            data['dt'] = int(time.time() * 1000)
            content = json.dumps(data)
            if data['code'] == 2:
                self.save_msg(content)
            # 调用广播，把消息推送给所有的客户端
            self.broadcast(self.pools, content)
        except Exception as e:
            print(e)

    # 3.关闭连接
    def on_close(self):
        # 连接从连接池删除
        self.pools.remove(self)

    def save_msg(self, content):
        session = ORM.db()
        try:
            msg = Message(
                content=content,
                create_time=int(time.time() * 1000),
                update_time=int(time.time() * 1000)
            )
            session.add(msg)
        except Exception:
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()


class MessageHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        data = self.get_message()
        result = []
        for v in data:
            result.append(json.loads(v.content))  # 转化为字典追加

        self.write(
            dict(
                data=result
            )
        )

    def get_message(self):
        session = ORM.db()
        data = []
        try:
            data = session.query(Message).order_by(
                "create_time"
            ).desc().limit(200).all()
        except Exception as e:
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()
        return data
