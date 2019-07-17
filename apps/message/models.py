from peewee import *
from intellectual_bloom.models import BaseModel
from apps.users.models import User


class Message(BaseModel):
    MESSAGE_COMMENT = 1
    MESSAGE_REPLY = 2
    MESSAGE_LIKE = 3
    MESSAGE_ANSWER = 4
    MESSAGE_ANSWER_REPLY = 5
    MESSAGE_TYPE = (
        (MESSAGE_COMMENT, "评论"),
        (MESSAGE_REPLY, "帖子回复"),
        (MESSAGE_LIKE, "点赞"),
        (MESSAGE_ANSWER, "回答"),
        (MESSAGE_ANSWER_REPLY, "回答的回复")
    )
    sender = ForeignKeyField(User, verbose_name="发送者")
    receiver = ForeignKeyField(User, verbose_name="接收者")
    message_type = SmallIntegerField(choices=MESSAGE_TYPE, verbose_name="类别")
    message = CharField
