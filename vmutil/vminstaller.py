from util import get_opt, mkdir
from kernelparam import KernelParam
from subprocess import call
from subprocess import Popen, PIPE, STDOUT
from debian import DebianPreseed
from configbase import ConfigBase
import gz

class VmInstallerBase(ConfigBase):
    def __init__(self, spec, vm):
        self.spec = spec
        self.vm = vm

    """Prepare the installer cdrom image. optionally mount it"""
    def prepare_cdrom(self):
        # add the boot cdrom
        disk = self.vm.add_disk_spec({
                'type': 'iso-image',
                'name': 'cdrom0',
                'file': self.get_property('cdrom/iso'),
                'url' : self.get_property('cdrom/url'),
            })
        disk.init_image()
        self.vm.set_property('bootdev', 'cdrom0')
        self.cdrom_image = disk.get_image_file()

    """extract a file from cdrom image"""
    def cdrom_extract(self, fn, out):
        print "Extracting cdrom file \""+fn+"\" to \""+out+"\""
        output = open(out, "w")
        p = Popen(["isoinfo", "-i", self.cdrom_image, "-x", fn], stdout=output)
        print p.communicate()
        return out

    """make a temp copy of initrd, either from cdrom or directly specified file"""
    def copy_initrd(self):
        initrd_cdrom = self.get_property('cdrom/initrd')
        initrd_gz_tmp = self.vm.get_tmpdir()+"/initrd.gz"
        if initrd_cdrom is None:
            initrd_gz_src = self.get_property('initrd')
            call(["cp", initrd_gz_src, initrd_gz_tmp])
            call(["chmod", "u+rw", initrd_gz_tmp])
        else:
            self.cdrom_extract(initrd_cdrom, initrd_gz_tmp)
        return initrd_gz_tmp

    def run(self):
        self.initVM()
        self.vm.start()

class VmInstallerDebian(VmInstallerBase):
    def __init__(self, spec, vm):
        VmInstallerBase.__init__(self, spec, vm)

        """ default kernel parameters """
        self.std_kparm = {
            'vga':                       'normal',
            'fb':                        'false',
            'recommends':                'false',
            'modules':                   'openssh-client-udeb',
            'DEBIAN_FRONTEND':           'text',
            'console':                   'ttyS0',

            'debian-installer/language': 'en',
            'country':                   'DE',
        }

        """ maps our properties to kernel parameters """
        self.vm_kparm = {
            'hostname': 'hostname',
            'domain':   'domain',
            'locale':   'locale',
        }

        """ NOTE: all the keys here need to be present for calling set() on them,
            in order to have their type. Keys w/ None value will be omitted in
            the final preseed file."""
        self.preseed_list = {
            'popularity-contest': {
                'popularity-contest/participate':               [ 'boolean',     'false'               ],
            },
            'd-i': {
                'base-installer/install-recommends':            [ 'boolean',     'false'               ],
                'mirror/country':                               [ 'string',      'de'                  ],
                'mirror/http/proxy':                            [ 'string',      ''                    ],
                'mirror/http/hostname':                         [ 'string',      None,                 ],
                'mirror/http/directory':                        [ 'string',      None,                 ],

                # automatic partitioning
                'partman-auto/init_automatically_partition':    [ 'select',      'biggest_free'        ],
                'partman-auto/disk':                            [ 'string',      '/dev/sda'            ],
                'partman-auto/choose_recipe':                   [ 'select',      'atomic'              ],
                'partman-auto/method':                          [ 'string',      'regular'             ],
                'partman-partitioning/confirm_write_new_label': [ 'boolean',     'true'                ],
                'partman/choose_partition':                     [ 'select',      'finish'              ],
                'partman/confirm':                              [ 'boolean',     'true'                ],
                'partman/confirm_nooverwrite':                  [ 'boolean',     'true'                ],

                # clock
                'clock-setup/utc':                              [ 'boolean',     'true'                ],

                # bootloader
                'grub-installer/skip':                          [ 'boolean',     'false'               ],
                'grub-installer/only_debian':                   [ 'boolean',     'true'                ],
                'grub-installer/bootdev':                       [ 'string',      'default'             ],

                # automatic poweroff
                'debian-installer/exit/poweroff':               [ 'boolean',     'true'                ],
                'finish-install/reboot_in_progress':            [ 'note',        ''                    ],

                # hwdetect
                'hw-detect/load_firmware':                      [ 'boolean',     'false'               ],
                'hw-detect/start_pcmcia':                       [ 'boolean',     'false'               ],

                'keymap':                                       [ 'select',      None                  ],
                'keyboard-configuration/xkb-keymap':            [ 'select',      None                  ],
                'keyboard-configuration/layoutcode':            [ 'string',      None                  ],
                'console-setup/ask_detect':                     [ 'boolean',     'false'               ],

                'time/zone':                                    [ 'string',      'US'                  ],
            },
            'tasksel': {
                'tasksel/first':                                [ 'multiselect', 'minimal, ssh-server' ],
            },
            'keyboard-configuration': {
                'keyboard-configuration/layoutcode':            [ 'string',      'de'                  ],
            },
            'apt-mirror-setup': {
                'apt-setup/use_mirror':                         [ 'boolean',     'true'                ],
                'apt-setup/cdrom/set-first':                    [ 'boolean',     'false'               ],
                'apt-setup/cdrom/set-next':                     [ 'boolean',     'false'               ],
                'apt-setup/cdrom/set-failed':                   [ 'boolean',     'false'               ],
            }
        }

    def write_preseed(self, tmpdir):
        p = DebianPreseed(tmpdir+'/preseed.cfg', self.preseed_list)
        p.set_timezone(self.get_property('timezone'))
        p.set_http_mirror(self.get_property('deb/mirror/http/hostname'), self.get_property('deb/mirror/http/directory'))
        p.set_keymap(self.get_property('deb/keyboard/layout'))
        p.set_root_passwd(self.vm.get_property('init-root-passwd'))
        p.set_admin_user(self.vm.get_property('init-admin-user'), self.vm.get_property('init-admin-passwd'))
        p.finish()

    def prepare_initrd(self):
        tmpdir = self.vm.get_tmpdir()

        # create preseed.cfg
        self.write_preseed(tmpdir)

        # fetch and uncompress initrd
        initrd_tmp = tmpdir+"/initrd"
        initrd_gz_tmp = self.copy_initrd()
        gz.uncompress(initrd_gz_tmp)

        # add preseed.cfg
        p = Popen(['cpio', '-H', 'newc', '-o', '-A', '-F', 'initrd'], stdout=PIPE, stdin=PIPE, stderr=STDOUT, cwd=tmpdir)
        print p.communicate(input=b'preseed.cfg\n')[0].decode()

        # compress modified initrd
        gz.compress(initrd_tmp)
        self.vm.set_property('initrd', initrd_gz_tmp)

    def kernel_img_tmp(self):
        return self.vm.get_tmpdir()+"/vmlinuz"

    def prepare_kernel(self):
        kernel_cdrom = self.get_property('cdrom/kernel')
        if kernel_cdrom is None:
            self.vm.set_property('kernel', self.get_property('kernel'))
            return

        self.vm.set_property('kernel', self.cdrom_extract(kernel_cdrom, self.kernel_img_tmp()))

    def initVM(self):
        self.prepare_cdrom()

        # kernel parameters
        self.kernel_param = KernelParam(self.get_property('kernel-args'))

        # this doesn't override explict kernel params
        for kp, kv in self.vm_kparm.iteritems():
            self.kernel_param.add(kp, self.vm.get_property(kv))

        # add default values
        self.kernel_param.add_list(self.std_kparm)

        self.prepare_kernel()

##        self.vm.set_property('sercon', 'yes')
        self.vm.set_property('append', self.kernel_param.__str__())
        self.vm.set_property('dtb', self.get_property('dtb'))
        self.vm.init_diskimages()
        self.prepare_initrd()

        print "APPEND:"+self.vm.get_property('append')

installers = {
    'debian-netinst': VmInstallerDebian,
    'debian':         VmInstallerDebian,
}

def getInstaller(spec, vm):
    if 'type' not in spec:
        raise ValueError('no installer type')

    i = spec['type']

    if i not in installers:
        raise ValueError('unknown installer: '+i)

    return installers[i](spec, vm)
