from peewee import *
from bcrypt import hashpw, gensalt
from intellectual_bloom.models import BaseModel


class PasswordHash(bytes):
    def check_password(self, password):
        password = password.encode('utf-8')
        return hashpw(password, self) == self


class PasswordField(BlobField):
    def __init__(self, iterations=12, *args, **kwargs):
        if None in (hashpw, gensalt):
            raise ValueError('Missing library required for PasswordField: bcrypt')
        self.bcrypt_iterations = iterations
        self.raw_password = None
        super(PasswordField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        """Convert the python value for storage in the database."""
        if isinstance(value, PasswordHash):
            return bytes(value)

        if isinstance(value, str):
            value = value.encode('utf-8')
        salt = gensalt(self.bcrypt_iterations)
        return value if value is None else hashpw(value, salt)

    def python_value(self, value):
        """Convert the database value to a pythonic value."""
        if isinstance(value, str):
            value = value.encode('utf-8')

        return PasswordHash(value)


class User(BaseModel):
    GENDER_MALE = 0
    GENDER_FEMALE = 1
    GENDERS = (
        (GENDER_MALE, "男"),
        (GENDER_FEMALE, "女")
    )
    phone_num = CharField(max_length=11, verbose_name="手机号", index=True)
    password = PasswordField(verbose_name="密码")
    nick_name = CharField(max_length=20, null=True, verbose_name="昵称")
    head_portrait = CharField(max_length=150, null=True, verbose_name="头像")
    address = CharField(max_length=200, null=True, verbose_name="地址")
    description = TextField(null=True, verbose_name="个人说明")
    gender = SmallIntegerField(
        choices=GENDERS,
        null=True,
        default=GENDER_MALE,
        verbose_name="性别"
    )
