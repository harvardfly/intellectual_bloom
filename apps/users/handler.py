import json
import jwt
import os
import shortuuid
import aiofiles
from apps.core.utils import get_current_timestamp
from intellectual_bloom.handler import RedisHandler
from apps.users.forms import (
    SendMessageCodeForm,
    RegisterForm,
    LoginForm,
    ProfileForm,
    ChangePasswordForm
)
from apps.core.utils import (
    random_code,
    AsyncSmsApi,
    authenticated_async
)

from apps.users.models import User


class RegisterHandler(RedisHandler):
    async def post(self, *args, **kwargs):
        req_data = self.request.body.decode("utf-8")
        req_data = json.loads(req_data)
        nick_name = req_data.get("nick_name")
        regester_form = RegisterForm.from_json(req_data)
        res_data = {}
        if regester_form.validate():
            phone_num = regester_form.phone_num.data
            code = regester_form.code.data
            password = regester_form.password.data
            key = "{}:{}".format(phone_num, code)
            if not self.redis_conn.get(key):
                self.set_status(400)
                res_data["content"] = "验证码错误或已失效"
            else:
                try:
                    await self.application.objects.get(
                        User, phone_num=phone_num
                    )
                    self.set_status(400)
                    res_data["content"] = "用于已存在"
                except User.DoesNotExist:
                    user_obj = await self.application.objects.create(
                        User, phone_num=phone_num, password=password,
                        nick_name=nick_name
                    )
                    res_data["id"] = user_obj.id
                    res_data["content"] = "注册成功"

        else:
            res_data["content"] = regester_form.errors
        self.finish(res_data)


class SendMessageHandler(RedisHandler):
    async def post(self, *args, **kwargs):
        """
        异步发送短信验证码
        :param args:
        :param kwargs:
        :return:
        """
        req_data = self.request.body.decode("utf-8")
        req_data = json.loads(req_data)
        sms_form = SendMessageCodeForm.from_json(req_data)
        if sms_form.validate():
            phone_num = sms_form.phone_num.data
            code = random_code()
            send_code = AsyncSmsApi("d6c4ddbf50ab36611d2f52041a0b949e")
            result = await send_code.send_single_sms(code, phone_num)

            if result.get("code") != 0:
                self.set_status(400)
                res_data = {
                    "phone_num": phone_num,
                    "msg": result.get("msg")
                }
            else:
                # 将验证码写入到redis中
                self.redis_conn.set(
                    "{}:{}".format(phone_num, code), 1, 7 * 24 * 60 * 60
                )
                res_data = {
                    "phone_num": phone_num,
                    "msg": result.get("msg")
                }
        else:
            self.set_status(400)
            res_data = sms_form.errors

        self.finish(res_data)


class LoginHandler(RedisHandler):
    async def post(self, *args, **kwargs):
        req_data = self.request.body.decode("utf-8")
        req_data = json.loads(req_data)
        login_form = LoginForm.from_json(req_data)
        res_data = {}
        if login_form.validate():
            phone_num = login_form.phone_num.data
            password = login_form.password.data
            try:
                user_obj = await self.application.objects.get(
                    User, phone_num=phone_num
                )
                if not user_obj.password.check_password(password):
                    self.set_status(400)
                    res_data["content"] = "用户名或密码不正确"
                else:
                    payload = {
                        "id": user_obj.id,
                        "exp": get_current_timestamp()
                    }
                    token = jwt.encode(
                        payload,
                        self.settings["secret_key"],
                        algorithm="HS256"
                    )
                    res_data["id"] = user_obj.id
                    res_data["token"] = token.decode("utf8")
            except User.DoesNotExist:
                self.set_status(400)
                res_data["content"] = "用户名不存在"
        else:
            res_data["content"] = login_form.errors

        self.finish(res_data)


class ProfileHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取用户信息
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {
            "phone_num": self.current_user.phone_num,
            "nick_name": self.current_user.nick_name,
            "gender": self.current_user.gender,
            "address": self.current_user.address,
            "description": self.current_user.description
        }
        self.finish(res_data)

    @authenticated_async
    async def patch(self, *args, **kwargs):
        """
        修改个人信息  部分更新(密码和账号不能修改)
        :param args:
        :param kwargs:
        :return:
        """
        req_data = self.request.body.decode("utf-8")
        req_data = json.loads(req_data)
        profile_form = ProfileForm.from_json(req_data)
        res_data = {}
        if profile_form.validate():
            self.current_user.nick_name = profile_form.nick_name.data
            self.current_user.gender = profile_form.gender.data
            self.current_user.address = profile_form.address.data
            self.current_user.description = profile_form.description.data
            await self.application.objects.update(self.current_user)
        else:
            self.set_status(400)
            for field in profile_form.errors:
                res_data[field] = profile_form.errors[field][0]
        self.finish(res_data)


class HeaderImagesHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        获取用户图像
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {
            "image": "/media/" + self.current_user.head_portrait
        }
        self.finish(res_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        修改个人图像
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        files_meta = self.request.files.get("image")
        if not files_meta:
            self.set_status(400)
            res_data["image"] = "请上传图片"
        else:
            for meta in files_meta:
                filename = meta["filename"]
                new_filename = "{uuid}_{filename}".format(
                    uuid=shortuuid.uuid(), filename=filename
                )
                file_path = os.path.join(
                    self.settings["MEDIA_ROOT"], new_filename
                )
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(meta['body'])
                    res_data["image"] = "/media/" + new_filename
                self.current_user.head_portrait = new_filename
                await self.application.objects.update(self.current_user)

        self.finish(res_data)


class PasswordHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        修改密码
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        req_data = self.request.body.decode("utf-8")
        req_data = json.loads(req_data)
        password_form = ChangePasswordForm.from_json(req_data)
        if password_form.validate():
            if not self.current_user.password.check_password(
                    password_form.old_password.data
            ):
                self.set_status(400)
                res_data["old_password"] = "旧密码错误"
            else:
                if password_form.new_password.data != password_form.confirm_password:
                    self.set_status(400)
                    res_data["new_password"] = "两次密码不一致"
                else:
                    self.current_user.password = password_form.new_password.data
                    await self.application.objects.update(self.current_user)
        else:
            self.set_status(400)
            for field in password_form.errors:
                res_data[field] = password_form.errors[field][0]

        self.finish(res_data)
