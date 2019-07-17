import random
import re
import math
import json
import time
import jwt
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from urllib.parse import quote_plus
from base64 import decodebytes, encodebytes
from urllib.parse import urlencode
from tornado import httpclient
from tornado.httpclient import HTTPRequest

from apps.users.models import User
from playhouse.shortcuts import model_to_dict

PHONE_NUM_REGEX = "^1[3456789]\d{9}$"

CATEGORY = {
    "life": "生活方式",
    "economics": "经济学",
    "sport": "运动",
    "IT": "互联网",
    "food": "美食",
    "edu": "教育",
    "news": "新闻",
    "helath": "健康",
    "business": "商业"
}


def random_code():
    """
    生成随机4位数字的验证码
    :return:
    """
    seeds = "0123456789"
    random_str = []
    for i in range(4):
        random_str.append(random.choice(seeds))
    return "".join(random_str)


class AsyncSmsApi(object):
    """
    使用第三方API异步发送短信
    """

    def __init__(self, api_key):
        self.api_key = api_key

    async def send_single_sms(self, code, mobile):
        http_client = httpclient.AsyncHTTPClient()
        url = "https://sms.yunpian.com/v2/sms/single_send.json"
        text = "您的验证码是{}。如非本人操作，请忽略本短信".format(code)
        post_request = HTTPRequest(url=url, method="POST", body=urlencode({
            "apikey": self.api_key,
            "mobile": mobile,
            "text": text
        }))
        try:
            res = await http_client.fetch(post_request)
            res_data = json.loads(res.body.decode("utf8"))
        except Exception:
            res_data = {"code": 1, "msg": "发送失败,请稍后再试!"}
        return res_data


def is_password(password):
    """
    验证密码格式问题, 能匹配的组合为：数字+字母，数字+特殊字符，
    字母+特殊字符，数字+字母+特殊字符组合，
    不能是纯数字，纯字母，纯特殊字符,密码长度为6至16位
    :param password:
    :return:
    """
    # return True if re.match(
    #     "^(?![\d]+$)(?![a-zA-Z]+$)(?![^\da-zA-Z]+$).{6,16}$",
    #     password
    # ) else False
    return True if re.match(
        "^.{6,16}$",
        password
    ) else False


def get_current_timestamp():
    """
    获取当前时间戳
    :return:
    """
    return int(time.time() * 1000)


def get_int_or_none(val):
    try:
        return int(val)
    except Exception:
        return None


def authenticated_async(func):
    """
    重写tornado authenticated
    :param func:
    :return:
    """

    async def wrapper(self, *args, **kwargs):
        res_data = {}
        token = self.request.headers.get("token")
        if token:
            try:
                send_data = jwt.decode(
                    token, self.settings["secret_key"],
                    leeway=self.settings["jwt_expire"],
                    options={"verify_exp": True}
                )
                user_id = send_data["id"]

                # 从数据库中获取到user并设置给_current_user
                try:
                    user = await self.application.objects.get(
                        User, id=user_id
                    )
                    self._current_user = user

                    # 此处很关键
                    result = await func(self, *args, **kwargs)
                    return result
                except User.DoesNotExist:
                    res_data["content"] = "用户不存在"
                    self.set_status(401)
            except Exception as e:
                print(e)
                self.set_status(401)
                res_data["content"] = "token不合法或已过期"
        else:
            self.set_status(401)
            res_data["content"] = "缺少token"

        self.write(res_data)

    return wrapper


def format_arguments(arguments):
    """
    以request.body_arguments 或者 request.arguments传参时
    将二进制转化utf-8编码
    :param arguments:
    :return:
    """

    data = {
        k: list(
            map(
                lambda val: str(val, encoding="utf-8"),
                v
            )
        )
        for k, v in arguments.items()
    }
    return data


def get_page(model, *args, **kwargs):
    """
    定义分页方法
    :param model:
    :param args:
    :param kwargs:
    :return:
    """
    # 获取页码
    page = kwargs.get("page") or 1
    per_page = kwargs.get("per_page") or 10
    # 统计数据表中有多少条记录
    total = len(model)
    if total:
        # 确定总共显示多少页
        pagenum = int(math.ceil(total / per_page))
        # 判断小于第一页
        if page < 1:
            page = 1
        # 判断大于最后一页
        if page > pagenum:
            page = pagenum

        # sql限制查询，每次查询限制多少条，偏移量是多少
        offset = (page - 1) * per_page
        # 分页查询
        data = model.limit(per_page).offset(offset)
        # 上一页
        prev_page = page - 1
        next_page = page + 1
        if prev_page < 1:
            prev_page = 1
        if next_page > pagenum:
            next_page = pagenum
        arr = dict(
            pagenum=pagenum,
            page=page,
            prev_page=prev_page,
            next_page=next_page,
            data=[model_to_dict(da) for da in data]
        )
    else:
        arr = dict(
            data=[]
        )
    return arr


class AliPay(object):
    """
    支付宝支付接口
    """

    def __init__(self, appid, app_notify_url, app_private_key_path,
                 alipay_public_key_path, return_url, debug=False):
        self.appid = appid
        self.app_notify_url = app_notify_url
        self.app_private_key_path = app_private_key_path
        self.app_private_key = None
        self.return_url = return_url
        with open(self.app_private_key_path) as fp:
            self.app_private_key = RSA.importKey(fp.read())

        self.alipay_public_key_path = alipay_public_key_path
        with open(self.alipay_public_key_path) as fp:
            self.alipay_public_key = RSA.import_key(fp.read())

        if debug is True:
            self.__gateway = "https://openapi.alipaydev.com/gateway.do"
        else:
            self.__gateway = "https://openapi.alipay.com/gateway.do"

    def direct_pay(self, subject, out_trade_no, total_amount, **kwargs):  # NOQA
        """
        构造请求参数biz_content，
        并将其放入公共请求参数中，
        返回签名sign的data
        :param subject:
        :param out_trade_no:
        :param total_amount:
        :param kwargs:
        :return:
        """
        biz_content = {
            "subject": subject,
            "out_trade_no": out_trade_no,
            "total_amount": total_amount,
            "product_code": "FAST_INSTANT_TRADE_PAY",
        }

        biz_content.update(kwargs)
        data = self.build_body(
            "alipay.trade.page.pay",
            biz_content,
            self.return_url
        )
        return self.sign_data(data)

    def build_body(self, method, biz_content, return_url=None):
        """
        构造公共请求参数
        :param method:
        :param biz_content:
        :param return_url:
        :return:
        """
        data = {
            "app_id": self.appid,
            "method": method,
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": biz_content
        }

        if return_url:
            data["notify_url"] = self.app_notify_url
            data["return_url"] = self.return_url

        return data

    def sign_data(self, data):
        """
        拼接排序后的data,以&连接成符合规范的字符串，并对字符串签名，
        将签名后的字符串通过quote_plus格式化，
        将请求参数中的url格式化为safe的，获得最终的订单信息字符串
        :param data:
        :return:
        """
        # 签名中不能有sign字段
        if "sign" in data:
            data.pop("sign")

        unsigned_items = self.ordered_data(data)
        unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)
        sign = self.sign_string(unsigned_string.encode("utf-8"))
        quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in unsigned_items)

        signed_string = quoted_string + "&sign=" + quote_plus(sign)
        return signed_string

    def ordered_data(self, data):
        """
        将请求参数字典排序，
        支付宝接口要求是拼接的有序参数字符串
        :param data:
        :return:
        """
        complex_keys = []
        for key, value in data.items():
            if isinstance(value, dict):
                complex_keys.append(key)

        for key in complex_keys:
            data[key] = json.dumps(data[key], separators=(',', ':'))

        return sorted([(k, v) for k, v in data.items()])

    def sign_string(self, unsigned_string):
        """
        生成签名,并进行base64 编码，
        转换为unicode表示并去掉换行符
        :param unsigned_string:
        :return:
        """
        key = self.app_private_key
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(SHA256.new(unsigned_string))
        sign = encodebytes(signature).decode("utf8").replace("\n", "")
        return sign

    def _verify(self, raw_content, signature):
        """
        对支付宝接口返回的数据进行签名比对，
        验证是否来源于支付宝
        :param raw_content:
        :param signature:
        :return:
        """
        key = self.alipay_public_key
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        digest.update(raw_content.encode("utf8"))
        if signer.verify(digest, decodebytes(signature.encode("utf8"))):
            return True
        return False

    def verify(self, data, signature):
        """
        验证支付宝返回的数据，防止是伪造信息
        :param data:
        :param signature:
        :return:
        """
        if "sign_type" in data:
            data.pop("sign_type")
        unsigned_items = self.ordered_data(data)
        message = "&".join(u"{}={}".format(k, v) for k, v in unsigned_items)
        return self._verify(message, signature)
