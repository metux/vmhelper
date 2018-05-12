from util import parse_size
from util import init_sparse_file
from configbase import ConfigBase

class Disk(ConfigBase):
    def __init__(self, spec, vm):
        self.spec = spec
        self.vm = vm

    def get_name(self):
        return self.spec['name']

    def get_image_file(self):
        return self.get_property('file')

    def get_size(self):
        return parse_size(self.spec['size'])

class DiskRaw(Disk):
    def __init__(self, spec, vm):
        Disk.__init__(self, spec, vm)

    def get_image_file(self):
        if 'file' in self.spec:
            return self.vm.vm_path+"/"+self.get_property('file')

        fn = self.vm.vm_path+"/"+self.get_property('name')+".raw"
        print "guessing filename: "+fn
        return fn

    def init_image(self):
        if init_sparse_file(self.get_image_file(), self.get_size()):
            print "initialized disk image: "+self.get_image_file()
            return True
        else:
            return False

class DiskISO(Disk):
    def __init__(self, spec, vm):
        Disk.__init__(self, spec, vm)

    def get_image_file(self):
        return self.vm.conf.get_iso_path()+"/"+self.get_property('file')

def getDisk(spec, vm):
    if spec['type'] == 'iso-image':
        return DiskISO(spec, vm)
    if spec['type'] == 'raw-image':
        return DiskRaw(spec, vm)
