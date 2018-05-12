from util import parse_size
from util import init_sparse_file

class VmConfigDisk:
    def __init__(self, cf, vm):
        self._my_cf = cf
        self._my_vm = vm

    def get_name(self):
        return self._my_cf['name']

    def get_image_file(self):
        if self._my_cf['type'] == 'iso-image':
            return "iso-images/"+self._my_cf['file']
        if self._my_cf['type'] == 'raw-image':
            return self._my_vm.vm_path+"/"+self._my_cf['file']
        return None

    def get_size(self):
        return parse_size(self._my_cf['size'])

    def init_image(self):
        if init_sparse_file(self.get_image_file(), self.get_size()):
            print "initialized disk image: "+self.get_image_file()
            return True
        else:
            return False
