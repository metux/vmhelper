import yaml
from util import get_opt
from util import get_opt_bool

class ConfigBase(object):

    def __init__(self, spec, filename = None):
        self.spec = spec
        if filename is not None:
            with open(filename) as text:
                self.spec = yaml.safe_load(text)

    def get_property_bool(self, key):
        return get_opt_bool(self.spec, key)

    def get_property(self, key):
        return get_opt(self.spec, key)

    def set_property(self, key, value):
        if value is not None:
            self.spec[key] = value
