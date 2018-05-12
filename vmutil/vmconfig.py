import yaml
from util import get_opt, get_opt_bool, mkdir
from configbase import ConfigBase
from disk import getDisk
from vmqemu import VmQemu
from vminstaller import getInstaller

class VmConfig(ConfigBase):

    def __init__(self, conf, name):
        self.conf    = conf
        self.name    = name
        self.vm_path = conf.vm_conf_prefix+"/"+name+"/"
        self.vm_cf   = self.vm_path+"vm.yml"

        with open(self.vm_cf) as text:
            self.spec = yaml.safe_load(text)

        self.disks = {}
        for d in self.spec['disks']:
            self.add_disk(getDisk(d, self))
        self.installer = getInstaller(self.spec['installer'], self)

        self.hv = VmQemu(self)

    def add_disk(self, dsk):
        self.disks[dsk.get_name()] = dsk

    def find_disk(self, name):
        return get_opt(self.disks, name)

    def get_disk_file(self, name):
        dsk = self.find_disk(name)
        if dsk is None:
            return dsk
        else:
            return dsk.get_image_file()

    def get_property_bool(self, key):
        return get_opt_bool(self.spec, key)

    def get_property(self, key):
        return get_opt(self.spec, key)

    def set_property(self, key, value):
        if value is not None:
            self.spec[key] = value

    def init_diskimages(self):
        dsk = self.find_disk("disk0")
        if dsk is None:
            print "no disk0"
            return False
        dsk.init_image()

    def setup(self):
        self.init_diskimages()

    def start(self):
        self.setup()
        self.hv.start()

    def get_tmpdir(self):
        dn = self.conf.get_tmpdir()+"/vm/"+self.name
        mkdir(dn)
        return dn
