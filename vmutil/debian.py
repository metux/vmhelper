class DebianPreseed(object):
    def __init__(self, fn, db = {} ):
        self.fn = fn
        self.db = db

    """Set preseed value. must already be defined in db. skips None values"""
    def set(self, cat, name, value):
        if value is not None:
            self.db[cat][name][1] = value

    """Set preseed value w/ type. skips None values"""
    def setx(self, cat, name, typ, value):
        if value is not None:
            self.db[cat][name] = [ typ, value ]

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

    def finish(self):
        fp = open(self.fn, 'w+')
        for cat, v1 in self.db.iteritems():
            for name, v2 in v1.iteritems():
                if v2[1] is not None:
                    s = "%-22s %-44s %-10s %s\n" % (cat,name,v2[0],v2[1])
                    fp.write(s)
        fp.close()

    def set_keymap(self, keymap):
        self.set('d-i', 'keymap',                            keymap)
        self.set('d-i', 'keyboard-configuration/xkb-keymap', keymap)
        self.set('d-i', 'keyboard-configuration/layoutcode', keymap)

    def set_http_mirror(self, hostname, directory):
        self.set('d-i', 'mirror/http/hostname',              hostname)
        self.set('d-i', 'mirror/http/directory',             directory)

    def set_timezone(self, tz):
        self.set('d-i', 'time/zone',                         tz)

    def set_root_passwd(self, pw):
        if pw is not None:
            self.setx('d-i', "passwd/root-login",             'boolean',  'true')
            self.setx('d-i', "passwd/root-password",          'password', pw)
            self.setx('d-i', "passwd/root-password-again",    'password', pw)

    def set_admin_user(self, name, pw):
        if (name is not None) and (pw is not None):
            self.setx('d-i', "passwd/make-user",              'boolean',  'true')
            self.setx('d-i', 'passwd/user-password',          'password', pw)
            self.setx('d-i', 'passwd/user-password-again',    'password', pw)
            self.setx('d-i', 'passwd/username',               'string',   name)
            self.setx('d-i', 'passwd/user-fullname',          'string',   name)
