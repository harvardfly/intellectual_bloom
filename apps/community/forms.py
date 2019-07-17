from wtforms_tornado import Form
from wtforms import StringField
from wtforms.validators import (
    DataRequired, AnyOf, Length
)

from apps.core.utils import CATEGORY


class CommunityGroupForm(Form):
    name = StringField(
        "小组名称",
        validators=[DataRequired(message="请输入小组名称"), ]
    )
    category = StringField(
        "小组类别",
        validators=[AnyOf(values=CATEGORY)]
    )


class GroupMemberForm(Form):
    apply_reason = StringField(
        "申请理由",
        validators=[DataRequired("请输入申请理由")]
    )


class PostForm(Form):
    title = StringField(
        "帖子标题",
        validators=[DataRequired("请输入帖子标题")]
    )
    content = StringField(
        "帖子内容",
        validators=[DataRequired("请输入帖子内容")]
    )


class CommentForm(Form):
    content = StringField(
        "评论内容",
        validators=[
            DataRequired("请输入评论内容"),
            Length(min=5, message="内容不少于5个字符")
        ]
    )


class ReplyForm(Form):
    content = StringField(
        "回复内容",
        validators=[DataRequired("请输入回复内容")]
    )
