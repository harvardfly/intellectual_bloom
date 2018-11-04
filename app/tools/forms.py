# coding:utf-8

from wtforms import Form
from wtforms.fields import (
    StringField, PasswordField, IntegerField
)
from wtforms.validators import (
    DataRequired, EqualTo, Email, Regexp, ValidationError
)
from app.emum_list import (
    SEX_FIELDS, CONSTELLATION
)

from .orm import ORM
from app.models.models import (User)


class RegistForm(Form):
    session = ORM.db()
    username = StringField(
        "昵称", validators=[DataRequired('昵称不能为空！')]
    )
    password = PasswordField(
        "密码", validators=[DataRequired("密码不能为空！")]
    )
    repwd = PasswordField(
        "确认密码", validators=[
            DataRequired("确认密码不能为空！"),
            EqualTo('password', message="两次输入密码不一致！")
        ]
    )
    email = StringField("邮箱", validators=[
        DataRequired("邮箱不能为空！"),
        Email("邮箱格式不正确！")
    ])
    phone_num = StringField("手机号", validators=[
        DataRequired("手机号不能为空！"),
        Regexp("1[3456789]\\d{9}", message="手机格式不正确！")
    ])

    constellation = IntegerField("星座")
    head_portrait = StringField("头像")
    sign_info = StringField("个性签名")
    sex = IntegerField("性别")

    # 自定义验证昵称
    def validate_username(self, field):
        user_obj = self.session.query(User).filter_by(username=field.data).first()
        if user_obj:
            raise ValidationError("用户名已经存在！")

    # 自定义验证邮箱
    def validate_email(self, field):
        user_obj = self.session.query(User).filter_by(email=field.data).first()
        if user_obj:
            raise ValidationError("邮箱已经存在！")

    # 自定义验证手机
    def validate_phone_num(self, field):
        user_obj = self.session.query(User).filter_by(phone_num=field.data).first()
        if user_obj:
            raise ValidationError("手机号已经存在！")

    def validate_sex(self, field):
        if field.data and field.data not in dict(SEX_FIELDS):
            raise ValidationError("性别必须在可选范围内")

    def validate_constellation(self, field):
        if field.data and field.data not in dict(CONSTELLATION):
            raise ValidationError("星座必须在可选范围内")


# 定义登录表单验证模型
class LoginForm(Form):
    session = ORM.db()
    username = StringField(
        "昵称", validators=[DataRequired('用户名不能为空！')]
    )
    password = PasswordField(
        "密码", validators=[DataRequired("密码不能为空！")]
    )

    def validate_pwd(self, field):
        user = self.session.query(User).filter_by(username=self.username.data).first()
        if not user or user.password != field.data:
            raise ValidationError("用户名不存在或密码不正确！")


# 定义个人资料编辑验证表单模型
class UserProfileEditForm(Form):
    session = ORM.db()
    id = IntegerField(
        "编号",
        validators=[
            DataRequired("编号不能为空！")
        ]
    )
    username = StringField(
        "昵称", validators=[DataRequired('昵称不能为空！')]
    )
    email = StringField("邮箱", validators=[
        DataRequired("邮箱不能为空！"),
        Email("邮箱格式不正确！")
    ])
    phone_num = StringField("手机号", validators=[
        DataRequired("手机号不能为空！"),
        Regexp("1[3456789]\\d{9}", message="手机格式不正确！")
    ])
    head_portrait = StringField("头像")
    sign_info = StringField("个性签名")
    sex = IntegerField("性别")
    constellation = IntegerField(
        "星座",
        validators=[
            DataRequired("星座不能为空！")
        ]
    )

    def validate_sex(self, field):
        if field.data and field.data not in dict(SEX_FIELDS):
            raise ValidationError("性别必须在可选范围内")

    def validate_constellation(self, field):
        if field.data and field.data not in dict(CONSTELLATION):
            raise ValidationError("星座必须在可选范围内")
