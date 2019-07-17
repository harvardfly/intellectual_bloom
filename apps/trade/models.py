import random
import time
from peewee import *
from intellectual_bloom.models import BaseModel
from apps.users.models import User


class OrderInfo(BaseModel):
    """
    订单
    """
    ORDER_STATUS = (
        ("TRADE_SUCCESS", "成功"),
        ("TRADE_CLOSED", "超时关闭"),
        ("WAIT_BUYER_PAY", "交易创建"),
        ("TRADE_FINISHED", "交易结束"),
        ("paying", "待支付"),
    )

    user = ForeignKeyField(User, verbose_name="用户")
    order_sn = CharField(
        max_length=30, null=True,
        unique=True, verbose_name="订单号"
    )
    trade_no = CharField(max_length=100, unique=True, null=True, verbose_name=u"交易号")
    pay_status = CharField(choices=ORDER_STATUS, default="paying", max_length=30, verbose_name="订单状态")
    post_script = CharField(max_length=200, verbose_name="订单留言")
    order_mount = FloatField(default=0.0, verbose_name="订单金额")
    pay_time = DateTimeField(null=True, verbose_name="支付时间")

    @classmethod
    def generate_order_sn(cls):
        # 当前时间+userid+随机数
        random_ins = random.Random()
        order_sn = "{}{}".format(
            time.strftime("%Y%m%d%H%M%S"),
            random_ins.randint(10, 99)
        )

        return order_sn
