class KernelParam:
    def __init__(self, spec):
        self.kparam = spec
        if self.kparam is None:
            self.kparam = {}
        if isinstance(self.kparam, str):
            raise ValueError("kparam must be a list")

    def add(self, kpar, kval):
        if (kval is not None) and (kpar not in self.kparam):
            self.kparam[kpar] = kval

    def add_list(self, klist):
        for kp, kv in klist.iteritems():
            self.add(kp, kv)

    def __str__(self):
        if len(self.kparam) == 0:
            return None

        buf = ""
        for kp, kv in self.kparam.iteritems():
            buf += kp+"="+kv+" "

        return buf
