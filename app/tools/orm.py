# -*- coding: utf-8 -*-
from sqlalchemy import create_engine  # 导入创建引擎
from sqlalchemy.orm import sessionmaker  # 创建会话工具
from app.settings import mysql_configs  # 导入连接配置


# 创建会话，操作数据表要通过会话操作
class ORM:
    @classmethod
    def db(cls):
        link = "mysql+mysqlconnector://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}?charset=utf8".format(
            **mysql_configs
        )
        # 创建连接引擎，encoding编码，echo是[True]否[False]输出日志
        engine = create_engine(
            link,
            encoding="utf-8",
            echo=False,
            pool_size=100,
            pool_recycle=10,
            connect_args={'charset': "utf8"}
        )
        # 创建用于操作数据表的会话
        Session = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=True,
            expire_on_commit=False
        )
        return Session()
