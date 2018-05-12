import yaml
from util import get_opt
from util import get_opt_bool
from vmconfigdisk import VmConfigDisk
from vmqemu import VmQemu
from vminstaller import getInstaller

class VmConfig:

    def __init__(self, name):
        self.load_vm_cf(name)
        self.hv = VmQemu(self)

    def load(self, fn, name):
        with open(fn) as text:
            self._my_cf = yaml.safe_load(text)
        self.vm_path="conf/vm/"+name
        self.disks = {}
        for d in self._my_cf['disks']:
            self.add_disk(VmConfigDisk(d, self))
        self.installer = getInstaller(self._my_cf['installer'], self)

    def load_vm_cf(self, name):
        self.load("conf/vm/"+name+"/vm.yml", name)

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

    def get_property_bool(self, pr):
        return get_opt_bool(self._my_cf, pr)

    def get_property(self, pr):
        return get_opt(self._my_cf, pr)

    def set_property(self, pr, val):
        if val is not None:
            self._my_cf[pr] = val

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
