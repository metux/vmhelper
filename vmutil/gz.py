from subprocess import call

def compress(fn):
    return call(["gzip", "-f", fn])

def uncompress(fn):
    return call(["gunzip", "-f", fn])
