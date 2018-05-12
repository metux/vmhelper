import re
from os import path

def parse_size(sz):
    if isinstance(sz,int):
        return sz

    res = re.compile(r'([0-9]+) *([kKmMgG])').split(sz)
    val = int(res[1])

    if res[2] == 'k' or res[2] == 'K':
        return val * 1024
    if res[2] == 'm' or res[2] == 'M':
        return val * 1024 * 1024
    if res[2] == 'g' or res[2] == 'G':
        return val * 1024 * 1024 * 1024

    raise ValueError('invalid size \'%s\'' % (sz))

def init_sparse_file(fn, size):
    if path.isfile(fn):
        return False

    if size is None:
        raise ValueError('missing size for image')

    fp = open(fn, 'a')
    fp.truncate(size)
    return True

def get_opt_bool(cf, attr):
    if attr in cf:
        if cf[attr] == 'yes':
            return True
        if cf[attr] == True:
            return True
    return False

def get_opt(cf, attr):
    if attr in cf:
        return cf[attr]
    else:
        return None

def flatten(param):
    if isinstance(param, dict):
        buf = ""
        for k in param:
            buf += k+"="+param[k]+" "
        return buf
    else:
        return buf
