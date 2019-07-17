from peewee import *
from intellectual_bloom.models import BaseModel
from apps.users.models import User


class Question(BaseModel):
    user = ForeignKeyField(User, verbose_name="用户")
    category = CharField(max_length=50, null=True, verbose_name="问题分类")
    title = CharField(max_length=150, null=True, verbose_name="标题")
    image = CharField(max_length=500, null=True, verbose_name="图片")
    content = TextField(null=True, verbose_name="内容")
    answer_nums = IntegerField(default=0, verbose_name="回答数")

    @classmethod
    def extend(cls):
        return cls.select(cls, User.id).join(User)


class Answer(BaseModel):
    # 回答和回复
    user = ForeignKeyField(User, verbose_name="用户", related_name="author")
    question = ForeignKeyField(Question, verbose_name="问题")
    parent_answer = ForeignKeyField('self', null=True, verbose_name="回答", related_name="answer_parent")
    reply_user = ForeignKeyField(User, verbose_name="用户", related_name="replyed_author", null=True)
    content = CharField(max_length=1000, verbose_name="内容")
    reply_nums = IntegerField(default=0, verbose_name="回复数")

    @classmethod
    def extend(cls):
        # 1. 多表join
        # 2. 多字段映射同一个model
        author = User.alias()
        relyed_user = User.alias()
        return cls.select(cls, Question, relyed_user.id, relyed_user.nick_name, author.id, author.nick_name).join(
            Question, join_type=JOIN.LEFT_OUTER, on=cls.question).switch(cls).join(author, join_type=JOIN.LEFT_OUTER,
                                                                                   on=cls.user).switch(cls).join(
            relyed_user, join_type=JOIN.LEFT_OUTER, on=cls.reply_user
        )
