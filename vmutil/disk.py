from os import path, rename
from util import parse_size
from util import init_sparse_file
from configbase import ConfigBase
import math
import urllib

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

def _url_report(blocks, blocksize, total):
    if (math.fmod(blocks, 1024)==0):
        print "   "+(str(blocks*blocksize/1024/1024))+"/"+str(total/1024/1024)+" MBytes"

class DiskISO(Disk):
    def __init__(self, spec, vm):
        Disk.__init__(self, spec, vm)

    def get_image_file(self):
        return self.vm.conf.get_iso_path()+"/"+self.get_property('file')

#    def get_mountpoint(self):

#    def mount(self):
#        iso = self.get_image_file(self)
#        name 
    def init_image(self):
        iso_fn  = self.get_image_file()
        iso_url = self.get_property('url')
        iso_tmp = iso_fn+".tmp"

        if path.isfile(iso_fn):
            print "ISO present: "+iso_fn
            return False

        if iso_url is None:
            if not path.isfile(iso_fn):
                raise("missing ISO file: "+iso_fn)
        else:
            print "Fetching ISO: "+iso_url
            res = urllib.urlretrieve(iso_url, iso_tmp, _url_report)
            print "ISO filename: "+res[0]
            rename(iso_tmp, iso_fn)
            return True

def getDisk(spec, vm):
    if spec['type'] == 'iso-image':
        return DiskISO(spec, vm)
    if spec['type'] == 'raw-image':
        return DiskRaw(spec, vm)
