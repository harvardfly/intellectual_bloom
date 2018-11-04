# coding:utf-8
import os
import time
import tornado.web
from uuid import uuid4
from app.tools.forms import (
    RegistForm, LoginForm, UserProfileEditForm
)
from app.tools.orm import ORM
from app.models.models import User
from werkzeug.datastructures import MultiDict


# 注册
class RegistHandler(tornado.web.RequestHandler):
    # 定义POST请求，专门处理注册表单
    def post(self, *args, **kwargs):
        data = self.fdata()
        form = RegistForm(data)
        res = {"code": 0}
        # 验证环节
        if form.validate():
            # 验证通过
            # 保存表单的数据到数据库user中去
            if self.save_regist_user(form):
                res["code"] = 1
        else:
            # 验证不通过
            res = form.errors
            res["code"] = 0
        self.write(res)  # 返回json接口信息

    def params(self):
        # 获取参数方式，里面是一些二进制信息，字典类型
        data = self.request.arguments
        # 定义二进制转化utf-8编码
        data = {
            k: list(
                map(
                    lambda val: str(val, encoding="utf-8"),
                    v
                )
            )
            for k, v in data.items()
            }
        return data

    # 定义表单接受数据类型
    def fdata(self):
        return MultiDict(self.params())

    def save_regist_user(self, form):
        # 创建会话
        session = ORM.db()
        try:
            user = User(
                username=form.data.get('username'),
                password=form.data.get('password'),
                email=form.data.get('email'),
                phone_num=form.data.get('phone_num'),
                sex=form.data.get('sex'),
                constellation=form.data.get('constellation'),
                head_portrait=form.data.get('head_portrait'),
                sign_info=form.data.get('sign_info'),
                create_time=int(time.time() * 1000),
                update_time=int(time.time() * 1000)
            )
            # 添加记录
            session.add(user)
        except Exception as e:
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()
        return True


# 登录
class LoginHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        data = self.fdata()
        form = LoginForm(data)
        res = {"code": 0}
        if form.validate():
            res["code"] = 1
        else:
            res = form.errors
            res["code"] = 0
        self.write(res)

    def params(self):
        # 获取参数方式，里面是一些二进制信息，字典类型
        data = self.request.arguments
        # 定义二进制转化utf-8编码
        data = {
            k: list(
                map(
                    lambda val: str(val, encoding="utf-8"),
                    v
                )
            )
            for k, v in data.items()
            }
        return data

    # 定义表单接受数据类型
    def fdata(self):
        return MultiDict(self.params())


# 个人资料视图
class UserProfileHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        data = self.fdata()
        form = UserProfileEditForm(data)
        res = {"code": 0}
        if form.validate():
            # 保存用户信息
            if self.save_user(form):
                res["code"] = 1
        else:
            res = form.errors
            res["code"] = 0
        self.write(res)

    def params(self):
        # 获取参数方式，里面是一些二进制信息，字典类型
        data = self.request.arguments
        # 定义二进制转化utf-8编码
        data = {
            k: list(
                map(
                    lambda val: str(val, encoding="utf-8"),
                    v
                )
            )
            for k, v in data.items()
            }
        return data

    # 定义表单接受数据类型
    def fdata(self):
        return MultiDict(self.params())

    def save_user(self, form):
        session = ORM.db()
        try:
            user = session.query(User).filter_by(
                id=int(form.data.get('id'))
            ).first()
            user.username = form.data.get('username')
            user.email = form.data.get('email')
            user.phone_num = form.data['phone_num']
            user.sex = int(form.data.get('sex'))
            user.constellation = int(form.data.get('constellation'))
            user.head_portrait = form.data['head_portrait']
            user.sign_info = form.data['sign_info']
            user.update_time = int(time.time() * 1000)
            session.add(user)
        except Exception:
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()
        return True


# 异步上传用户头像
class UploadHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        # 1.获取客户端上传的头像
        files = self.request.files.get("img")
        imgs = []
        # 2.定义保存目录
        upload_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)
            ), "static/uploads"
        )
        # 如果目录不存在则创建
        if not os.path.exists(upload_path):
            os.mkdir(upload_path)
        # 指定修改名称
        for v in files:
            prefix1 = int(time.time() * 1000)
            prefix2 = uuid4()
            newname = "{0}_{1}_{2}".format(
                prefix1, prefix2,
                os.path.splitext(v['filename'])[-1]
            )
            # 执行保存
            with open(os.path.join(upload_path, newname), "wb") as up:
                up.write(v["body"])
            imgs.append(newname)
        # 返回图片的接口
        self.write(
            dict(
                code=1,
                image=imgs[-1]
            )
        )
