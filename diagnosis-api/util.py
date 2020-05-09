import random
from datetime import datetime


def random_bytes(n):
    return bytes([random.getrandbits(8) for i in range(n)])


def generate_tek():
    return random_bytes(16)


def generate_authorization_key():
    return random_bytes(16)


def dt_to_enin(ts, window_minutes=10):
    return int(datetime.timestamp(ts) / (60 * window_minutes))


def now_to_enin():
    return dt_to_enin(datetime.now())

def generate_random_tek():
    randbytes = [random.getrandbits(8) for i in range(16)]
    return bytes(randbytes), now_to_enin()
