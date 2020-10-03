import random
import string


def rand_str(lens):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(lens)])
