from tornado.web import url
from apps.users.handler import (
    SendMessageHandler,
    RegisterHandler,
    LoginHandler,
    ProfileHandler,
    HeaderImagesHandler,
    PasswordHandler
)

urlpattern = (
    url("/code/", SendMessageHandler),
    url("/register/", RegisterHandler),
    url("/login/", LoginHandler),
    url("/info/", ProfileHandler),
    url("/headimages/", HeaderImagesHandler),
    url("/password/", PasswordHandler),
)
