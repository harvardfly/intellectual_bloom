from tornado.web import url
from apps.community.handler import (
    GroupsHandler,
    GroupListHandler,
    GroupMemberHandler,
    PostHandler,
    PostListHandler,
    CommentHandler,
    ReplyHandler,
    ReplyListHandler,
    CommentLikeHandler,
    ReplyLikeHandler
)

urlpattern = (
    url("/group/", GroupsHandler),
    url("/group_list", GroupListHandler),
    url("/group_member/", GroupMemberHandler),
    url("/post/", PostHandler),
    url("/post_list/", PostListHandler),
    url("/comment/", CommentHandler),
    url("/comment_list/", CommentHandler),
    url("/reply/", ReplyHandler),
    url("/reply_list/", ReplyListHandler),
    url("/comment_like/", CommentLikeHandler),
    url("/reply_like/", ReplyLikeHandler),
)
