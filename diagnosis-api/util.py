import random
import base64
from datetime import datetime


def generate_random_authority():
    """
    Generate random 16-byte ID

    Generated:
    '2iUNf7/8pjS/mzjpQwUIuw==\n'
    'V3Qpwr4TU7CICdwowL9rwA==\n'
    """
    randbytes = [random.getrandbits(8) for i in range(16)]
    return bytearray(randbytes)


def dt_to_enin(ts, window_minutes=10):
    return int(datetime.timestamp(ts) / (60 * window_minutes))


def now_to_enin():
    return dt_to_enin(datetime.now())


def generate_random_tek():
    randbytes = [random.getrandbits(8) for i in range(16)]
    return bytearray(randbytes), now_to_enin()

def encodeb64(byts):
    return base64.encodebytes(byts).decode('utf8').strip()
