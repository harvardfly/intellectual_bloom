# coding:utf-8

from app.views.views_user import (
    RegistHandler, LoginHandler,
    UserProfileHandler, UploadHandler,
)
from app.views.views_video import (
    ViewListHandler,
    PlayChatHandler
)
from app.views.views_chat import MessageHandler
from sockjs.tornado import SockJSRouter
from app.views.views_chat import ChatRoomHandler

urls = [
           (r"/regist/", RegistHandler),
           (r"/login/", LoginHandler),
           (r"/userprofile/", UserProfileHandler),
           (r"/upload/", UploadHandler),
           (r"/", ViewListHandler),
           (r"/playchat/", PlayChatHandler),
           (r"/message/", MessageHandler)
       ] + SockJSRouter(ChatRoomHandler, "/chat").urls
