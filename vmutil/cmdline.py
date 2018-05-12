class CmdLine:
    def __init__(self, prog):
        self.args = [ prog ]

    def opt_arg(self, par, val):
        if val is not None:
            self.args.append(par)
            self.args.append(val)

    def opt_sw(self, par, val):
        if val is not None:
            if val:
                self.args.append(par)
