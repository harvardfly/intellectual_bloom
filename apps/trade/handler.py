import json
from datetime import datetime
from intellectual_bloom.handler import BaseHandler
from apps.core.utils import AliPay
from intellectual_bloom.settings import settings
from apps.core.utils import format_arguments
from apps.trade.models import OrderInfo
from apps.core.utils import (
    authenticated_async,
    get_int_or_none
)
from apps.trade.forms import TradeOrderSnForm


class OrderSnHandler(BaseHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        """
        创建订单信息
        :param request:
        :return:
        """
        res_data = {}
        req_data = self.request.body.decode("utf8")
        req_data = json.loads(req_data)
        post_script = req_data.get("post_script")
        order_form = TradeOrderSnForm.from_json(req_data)
        if order_form.validate():
            try:
                order_mount = order_form.order_mount.data
                orders_object = await self.application.objects.create(
                    OrderInfo,
                    pay_status=OrderInfo.ORDER_STATUS[4][0],
                    pay_time=datetime.now(),
                    order_sn=OrderInfo.generate_order_sn(),
                    user=self.current_user,
                    order_mount=order_mount,
                    post_script=post_script
                )
                res_data["id"] = orders_object.id
            except Exception:
                self.set_status(400)
                res_data["content"] = "订单创建失败"
        else:
            res_data["content"] = order_form.errors

        self.finish(res_data)


class GenPayLinkHandler(BaseHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        """
        通过订单生成支付链接
        :param args:
        :param kwargs:
        :return:
        """
        res_data = {}
        order_id = get_int_or_none(self.get_argument("id", None))
        if not order_id:
            self.set_status(400)
            self.write({"content": "缺少order_id参数"})

        try:
            order_obj = await self.application.objects.get(
                OrderInfo, id=order_id,
                pay_status=OrderInfo.ORDER_STATUS[4][0]
            )
            out_trade_no = order_obj.order_sn
            order_mount = order_obj.order_mount
            subject = order_obj.post_script
            alipay = AliPay(
                appid=settings["ALI_APPID"],
                app_notify_url="{}/alipay/return/".format(settings["SITE_URL"]),
                app_private_key_path=settings["private_key_path"],
                alipay_public_key_path=settings["ali_pub_key_path"],
                debug=True,
                return_url="{}/alipay/return/".format(settings["SITE_URL"])
            )
            url = alipay.direct_pay(
                subject=subject,
                out_trade_no=out_trade_no,
                total_amount=order_mount,
                return_url="{}/alipay/return/".format(settings["SITE_URL"])
            )
            re_url = settings["RETURN_URI"].format(data=url)
            res_data["re_url"] = re_url
        except OrderInfo.DoesNotExist:
            self.set_status(400)
            res_data["content"] = "订单不存在"

        self.finish(res_data)


class AlipayHandler(BaseHandler):
    def get(self, *args, **kwargs):
        """
        处理支付宝的return_url返回
        :param request:
        :return:
        """
        res_data = {}
        processed_dict = {}
        req_data = self.request.arguments
        req_data = format_arguments(req_data)
        for key, value in req_data.items():
            processed_dict[key] = value[0]

        sign = processed_dict.pop("sign", None)
        alipay = AliPay(
            appid=settings["ALI_APPID"],
            app_notify_url="{}/alipay/return/".format(settings["SITE_URL"]),
            app_private_key_path=settings["private_key_path"],
            alipay_public_key_path=settings["ali_pub_key_path"],
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # 默认False,
            return_url="{}/alipay/return/".format(settings["SITE_URL"])
        )

        verify_re = alipay.verify(processed_dict, sign)

        if verify_re is True:
            res_data["content"] = "success"
        else:
            res_data["content"] = "Failed"

        self.finish(res_data)

    async def post(self, *args, **kwargs):
        """
        处理支付宝的notify_url
        :param request:
        :return:
        """
        processed_dict = {}
        req_data = self.request.body_arguments
        req_data = format_arguments(req_data)
        for key, value in req_data.items():
            processed_dict[key] = value[0]

        sign = processed_dict.pop("sign", None)
        alipay = AliPay(
            appid=settings["ALI_APPID"],
            app_notify_url="{}/alipay/return/".format(settings["SITE_URL"]),
            app_private_key_path=settings["private_key_path"],
            alipay_public_key_path=settings["ali_pub_key_path"],
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # 默认False,
            return_url="{}/alipay/return/".format(settings["SITE_URL"])
        )

        verify_re = alipay.verify(processed_dict, sign)

        if verify_re is True:
            order_sn = processed_dict.get('out_trade_no')
            trade_no = processed_dict.get('trade_no')
            trade_status = processed_dict.get('trade_status')

            orders_query = OrderInfo.update(
                pay_status=trade_status,
                trade_no=trade_no,
                pay_time=datetime.now()
            ).where(
                OrderInfo.order_sn == order_sn
            )
            await self.application.objects.execute(
                orders_query
            )

        self.finish("success")
