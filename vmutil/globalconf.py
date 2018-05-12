import yaml
from vmconfig import VmConfig
from configbase import ConfigBase

class GlobalConfig(ConfigBase):

    def __init__(self, confdir):
        ConfigBase.__init__(self, None, confdir+"/config.yml")
        self.vm_conf_prefix=confdir+"/vm/"

    def get_vm(self, name):
        return VmConfig(self, name)

    def get_iso_path(self):
        return self.spec['directories']['iso-images']

    def get_tmpdir(self):
        return self.spec['directories']['temp']
