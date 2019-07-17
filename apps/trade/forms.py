from wtforms_tornado import Form
from wtforms import (
    FloatField
)
from wtforms.validators import (
    DataRequired
)


class TradeOrderSnForm(Form):
    order_mount = FloatField(
        "订单金额",
        validators=[DataRequired(message="请输入订单金额"), ]
    )

