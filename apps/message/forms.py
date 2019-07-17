from wtforms_tornado import Form
from wtforms import StringField, IntegerField
from wtforms.validators import (
    DataRequired, Regexp, EqualTo, AnyOf
)
from wtforms.fields import (
    PasswordField
)
from apps.core.utils import PHONE_NUM_REGEX
from apps.users.models import User


class SendMessageCodeForm(Form):
    phone_num = StringField(
        "手机号码",
        validators=[
            DataRequired(message="请输入手机号码"),
            Regexp(PHONE_NUM_REGEX, message="请输入合法的手机号码")
        ]
    )


class RegisterForm(Form):
    phone_num = StringField(
        "手机号码",
        validators=[
            DataRequired(message="请输入手机号码"),
            Regexp(PHONE_NUM_REGEX, message="请输入合法的手机号码")
        ]
    )
    code = StringField(
        "验证码",
        validators=[
            DataRequired(message="请输入验证码")
        ]
    )
    password = PasswordField(
        "密码",
        validators=[
            DataRequired(message="请输入密码")
        ]
    )
    repwd = PasswordField(
        "确认密码", validators=[
            DataRequired("确认密码不能为空！"),
            EqualTo('password', message="两次输入密码不一致！")
        ]
    )


class LoginForm(Form):
    phone_num = StringField(
        "手机号码",
        validators=[
            DataRequired(message="请输入手机号码"),
            Regexp(PHONE_NUM_REGEX, message="请输入合法的手机号码")
        ]
    )
    password = PasswordField(
        "密码",
        validators=[
            DataRequired(message="请输入密码")
        ]
    )


class ProfileForm(Form):
    nick_name = StringField(
        "昵称",
        validators=[
            DataRequired(message="请输入昵称"),
        ]
    )
    gender = IntegerField(
        "性别",
        validators=[
            AnyOf(values=[User.GENDER_MALE, User.GENDER_FEMALE])
        ]
    )
    address = StringField(
        "地址",
        validators=[
            DataRequired(message="请输入地址"),
        ]
    )
    description = StringField(
        "个人说明"
    )


class ChangePasswordForm(Form):
    old_password = StringField(
        "密码",
        validators=[
            DataRequired(message="请输入密码"),
        ]
    )
    new_password = StringField(
        "新密码",
        validators=[
            DataRequired(message="请输入新密码"),
        ]
    )
    confirm_password = StringField(
        "确认密码",
        validators=[
            DataRequired(message="请输入确认密码"),
        ]
    )
