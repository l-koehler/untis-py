import time, base64, hmac, hashlib

# add parameters to URL in a stupid way
# spaces get replaced, the rest has to be fine :D
def concat_literal_params(url, params):
    first_val = True
    for key,value in params.items():
        value = value.replace(' ', '+')
        if first_val:
            first_val = False
            url += f"?{key}={value}"
        else:
            url += f"&{key}={value}"
    return url

# cryptic functions for webuntis
# from https://github.com/sapuseven/betteruntis (GPL3)
def verify_code(key: bytes, time: int) -> int:
    t = time
    array_of_byte = bytearray(8)

    for i in range(8):
        array_of_byte[7 - i] = t & 0xFF
        t >>= 8

    local_mac = hmac.new(key, array_of_byte, hashlib.sha1)
    hashed_key = local_mac.digest()
    k = hashed_key[19] & 0xFF
    t = 0

    for i in range(4):
        l = hashed_key[(k & 0xF) + i] & 0xFF
        t = (t << 8) | l

    return (t & 0x7FFFFFFF) % 1000000

def create_time_based_code(secret) -> int:
    timestamp = int(time.time() * 1000)
    if secret and len(secret) > 0:
        decoded_key = base64.b32decode(secret.upper(), casefold=True)
        return verify_code(decoded_key, timestamp // 30000)
    else:
        return 0
