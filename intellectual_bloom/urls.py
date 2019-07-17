from tornado.web import url
from tornado.web import StaticFileHandler
from intellectual_bloom.settings import settings
from apps.users import urls as user_urls
from apps.community import urls as community_urls
from apps.trade import urls as trade_urls
from apps.question import urls as question_urls

urlpattern = [
    (url("/media/(.*)", StaticFileHandler, {'path':settings["MEDIA_ROOT"]}))
]

urlpattern += user_urls.urlpattern
urlpattern += community_urls.urlpattern
urlpattern += trade_urls.urlpattern
urlpattern += question_urls.urlpattern