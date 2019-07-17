from peewee import *
from intellectual_bloom.models import BaseModel
from apps.users.models import User


class CommunityGroup(BaseModel):
    creator = ForeignKeyField(User, verbose_name="小组创建者")
    name = CharField(max_length=150, null=True, verbose_name="小组名称")
    category = CharField(max_length=50, null=True, verbose_name="小组分类")
    front_image = CharField(max_length=500, null=True, verbose_name="封面图")
    description = TextField(null=True, verbose_name="小组说明")
    notice = TextField(null=True, verbose_name="小组公告")
    member_nums = IntegerField(default=0, verbose_name="小组成员数")
    post_nums = IntegerField(default=0, verbose_name="帖子数")

    @classmethod
    def extend(cls):
        return cls.select(cls, User.id).join(User)


class CommunityGroupMember(BaseModel):
    Status = (
        (0, "待审核"),
        (1, "同意"),
        (-1, "拒绝")
    )
    user = ForeignKeyField(User, verbose_name="组成员")
    group = ForeignKeyField(CommunityGroup, verbose_name="所属小组")
    apply_reason = CharField(max_length=500, verbose_name="申请理由")
    status = SmallIntegerField(
        choices=Status,
        default=Status[0][0],
        verbose_name="审核状态"
    )
    handle_msg = CharField(max_length=200, null=True, verbose_name="审核意见")


class CommunityPost(BaseModel):
    user = ForeignKeyField(User, verbose_name="发帖人")
    title = CharField(max_length=200, verbose_name="标题")
    group = ForeignKeyField(CommunityGroup, verbose_name="所属小组")
    content = TextField(verbose_name="帖子内容")
    is_cream = BooleanField(default=0, verbose_name="是否精华帖")
    is_hot = BooleanField(default=0, verbose_name="是否热门帖")


class Comment(BaseModel):
    user = ForeignKeyField(User, verbose_name="评论人")
    post = ForeignKeyField(CommunityPost, verbose_name="帖子")
    content = TextField(verbose_name="内容")


class Reply(BaseModel):
    user = ForeignKeyField(User, verbose_name="回复人")
    comment = ForeignKeyField(Comment, verbose_name="评论", on_delete=True)
    content = TextField(verbose_name="回复的内容")


class CommentLike(BaseModel):
    user = ForeignKeyField(User, verbose_name="点赞人")
    status = SmallIntegerField(default=0, verbose_name="点赞状态")
    comment = ForeignKeyField(Comment, verbose_name="评论")


class ReplyLike(BaseModel):
    user = ForeignKeyField(User, verbose_name="点赞人")
    status = SmallIntegerField(default=0, verbose_name="点赞状态")
    reply = ForeignKeyField(Reply, verbose_name="回复", on_delete=True)
