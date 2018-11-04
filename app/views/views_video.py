# coding:utf-8
import math
import tornado.web
from app.tools.orm import ORM
from app.models.models import Video


class ViewListHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        data = {}
        session = ORM.db()
        name = self.get_argument("name", "")
        try:
            if name:
                model = session.query(Video).filter(
                    Video.name.contains(name)
                ).order_by(Video.create_time.desc())
            else:
                model = session.query(Video).order_by(
                    Video.create_time.desc()
                )
            data['video'] = self.page(model)

        except Exception:
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()

        self.write(data)

    # 定义分页方法
    def page(self, model):
        # 获取页码
        page = self.get_argument("page", 1)
        page = int(page)
        # 统计数据表中有多少条记录
        total = model.count()
        if total:
            # 每页显示多少条
            shownum = 15
            # 确定总共显示多少页
            pagenum = int(math.ceil(total / shownum))
            # 判断小于第一页
            if page < 1:
                page = 1
            # 判断大于最后一页
            if page > pagenum:
                page = pagenum

            # sql限制查询，每次查询限制多少条，偏移量是多少
            offset = (page - 1) * shownum
            # 分页查询
            data = model.limit(shownum).offset(offset)
            # 上一页
            prev_page = page - 1
            next_page = page + 1
            if prev_page < 1:
                prev_page = 1
            if next_page > pagenum:
                next_page = pagenum
            arr = dict(
                pagenum=pagenum,
                page=page,
                prev_page=prev_page,
                next_page=next_page,
                data=[{
                          "name": da.name,
                          "url": da.url,
                          "create_time": da.create_time,
                          "update_time": da.update_time,
                          "logo": da.logo
                      } for da in data]
            )
        else:
            arr = dict(
                data=[]
            )
        return arr


class PlayChatHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        id = self.get_argument("id", None)
        if id:
            da = self.video(id)
            data = {
                "name": da.name,
                "url": da.url,
                "create_time": da.create_time,
                "update_time": da.update_time,
                "logo": da.logo
            }
            self.write(data)

    def video(self, id):
        session = ORM.db()
        video = None
        try:
            video = session.query(Video).filter_by(id=int(id)).first()
        except Exception:
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()
        return video
