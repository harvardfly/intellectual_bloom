# -*- coding: utf-8 -*-
import redis  # 连接驱动
from app.settings import redis_configs


def get_redis_conn():
    # 连接池
    pool = redis.ConnectionPool(**redis_configs)
    conn = redis.Redis(connection_pool=pool)
    return conn
