import sys
import os

pre_current_dir = os.path.dirname(os.getcwd())
sys.path.append("{}/intellectual_bloom/".format(pre_current_dir))

from apps.users.models import User
from apps.community.models import (
    CommunityGroup,
    CommunityGroupMember,
    CommunityPost,
    Comment,
    Reply,
    CommentLike,
    ReplyLike
)
from apps.question.models import (
    Question,
    Answer
)
from apps.trade.models import OrderInfo
from intellectual_bloom.settings import database


def init():
    # 生成表
    database.create_tables([User], safe=True)
    database.create_tables([OrderInfo], safe=True)
    database.create_tables(
        [
            CommunityGroup, CommunityGroupMember,
            CommunityPost, Comment, Reply, CommentLike, ReplyLike
        ],
        safe=True)
    database.create_tables([Question, Answer], safe=True)


if __name__ == "__main__":
    init()
