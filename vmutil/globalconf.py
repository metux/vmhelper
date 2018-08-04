import yaml
from vmconfig import VmConfig
from configbase import ConfigBase

class GlobalConfig(ConfigBase):

    def __init__(self, confdir):
        ConfigBase.__init__(self, None, confdir+"/config.yml")
        self.confdir = confdir
        self.vm_conf_prefix=confdir+"/vm/"

    """load VmConfig for given vm name"""
    def get_vm(self, name):
        return VmConfig(self, name)

    """retrieve installer template by name"""
    def get_installer_tmpl(self, name):
        filename = self.confdir+"/installer/"+name+".yml"
        with open(filename) as text:
            return yaml.safe_load(text)

    def get_iso_path(self):
        return self.spec['directories']['iso-images']

    def get_tmpdir(self):
        return self.spec['directories']['temp']
