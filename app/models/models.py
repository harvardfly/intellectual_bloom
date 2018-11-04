# coding:utf-8

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import (
    INTEGER, VARCHAR, BIGINT, TINYINT
)
from werkzeug.security import check_password_hash  # 检查密码
from app.settings import mysql_configs

BaseModel = declarative_base()
metadata = BaseModel.metadata


class User(BaseModel):
    __tablename__ = "user"
    id = Column(INTEGER, primary_key=True)
    create_time = Column(BIGINT, nullable=False)
    update_time = Column(BIGINT, nullable=False)
    username = Column(VARCHAR(50), nullable=False, unique=True)
    password = Column(VARCHAR(255), nullable=False)
    email = Column(VARCHAR(100), nullable=False, unique=True)
    phone_num = Column(VARCHAR(11), nullable=False, unique=True)
    sex = Column(TINYINT, nullable=True, default=0)
    constellation = Column(TINYINT, nullable=True)  # 星座
    head_portrait = Column(VARCHAR(100), nullable=True)  # 头像
    sign_info = Column(VARCHAR(1000), nullable=True)  # 个性签名


class Video(BaseModel):
    __tablename__ = "video"
    id = Column(INTEGER, primary_key=True)
    create_time = Column(BIGINT, nullable=False)
    update_time = Column(BIGINT, nullable=False)
    name = Column(VARCHAR(255), nullable=False)  # 视频名称
    url = Column(VARCHAR(255), nullable=False)
    logo = Column(VARCHAR(255), nullable=False)  # 视频缩图


if __name__ == "__main__":
    from sqlalchemy import create_engine  # 创建连接引擎

    # 主机、端口、名称、用户、密码
    mysql_configs = mysql_configs
    # 连接信息，数据库类型+数据库连接驱动://用户:密码@主机:端口/数据库名称
    # {} 槽，占位符
    mysql_uri = "mysql+mysqlconnector://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}".format(
        **mysql_configs
    )
    # 创建连接引擎，encoding编码，echo是[True]否[False]输出日志
    engine = create_engine(
        mysql_uri,
        encoding="utf-8",
        echo=True
    )
    # 模型映射生成数据表
    metadata.create_all(engine)
