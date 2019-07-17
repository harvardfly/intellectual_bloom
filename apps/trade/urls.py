from tornado.web import url
from apps.trade.handler import (
    OrderSnHandler,
    AlipayHandler,
    GenPayLinkHandler
)

urlpattern = (
    url("/order/", OrderSnHandler),
    url("/pay_link/", GenPayLinkHandler),
    url("/alipay/return/", AlipayHandler),
)
