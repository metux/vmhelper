import yaml
from util import get_opt
from util import get_opt_bool
from vmconfig import VmConfig
from configbase import ConfigBase

class GlobalConfig(ConfigBase):

    def __init__(self, confdir):
        ConfigBase.__init__(self, None, confdir+"/config.yml")
        self.vm_conf_prefix=confdir+"/vm/"

    def get_vm(self, name):
        return VmConfig(self, name)
