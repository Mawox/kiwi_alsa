from redis import StrictRedis

redis_config = {"host":"35.198.72.72", "port":3389}

redis = StrictRedis(socket_connect_timeout=3, **redis_config)

redis.set("x", 5)

redis.get("x")