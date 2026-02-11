import redis
from config import REDIS_URL

r = redis.Redis.from_url(REDIS_URL)

def set_focus(user_id, end_time):
    r.set(f"focus:{user_id}", end_time)

def get_focus(user_id):
    return r.get(f"focus:{user_id}")

def clear_focus(user_id):
    r.delete(f"focus:{user_id}")
