import redis

from configuration import configuration

redis_connection = redis.Redis.from_url(configuration["redis_url"])
