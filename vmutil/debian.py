class DebianPreseed(object):
    def __init__(self, fn, db = {} ):
        self.fn = fn
        self.fp = open(fn, 'w+')
        self.db = db

    """Set preseed value. must already be defined in db. skips None values"""
    def set(self, cat, name, value):
        if value is not None:
            self.db[cat][name][1] = value

    def _add(self, cat, name, t, value, dflt = None):
        if cat not in self.db:
            self.db[cat] = {}

        if value is None:
            value = dflt
        if value is not None:
            self.db[cat][name] = [ t, value ]

    def add_list(self, lst):
        for cat, v1 in lst.iteritems():
            for name, v2 in v1.iteritems():
                self._add(cat, name, v2[0], v2[1])

    def write_db(self):
        for cat, v1 in self.db.iteritems():
            for name, v2 in v1.iteritems():
                if v2[1] is not None:
                    s = "%-18s %-44s %-10s %s\n" % (cat,name,v2[0],v2[1])
                    self.fp.write(s)

    def di_str(self, name, value):
        self._add("d-i", name, "string", value)

    def di_str_list(self, lst):
        for pn, pv in lst.iteritems():
            self.di_str(pn, pv)

    def finish(self):
        self.write_db()
        self.fp.close()

    def set_keymap(self, keymap):
        self.set('d-i', 'keymap',                            keymap)
        self.set('d-i', 'keyboard-configuration/xkb-keymap', keymap)
        self.set('d-i', 'keyboard-configuration/layoutcode', keymap)

    def set_http_mirror(self, hostname, directory):
        self.set('d-i', 'mirror/http/hostname',              hostname)
        self.set('d-i', 'mirror/http/directory',             directory)

    def set_timezone(self, tz):
        self.set('d-i', 'time/zone',                         tz)
