from util import get_opt, mkdir
from kernelparam import KernelParam
from subprocess import call
from subprocess import Popen, PIPE, STDOUT
from debian import DebianPreseed
from configbase import ConfigBase

class VmInstallerBase(ConfigBase):
    def __init__(self, spec, vm):
        self.spec = spec
        self.vm = vm

    """Prepare the installer cdrom image. optionally mount it"""
    def prepare_cdrom(self, mount=False):
        # add the boot cdrom
        disk = self.vm.add_disk_spec({
                'type': 'iso-image',
                'name': 'cdrom0',
                'file': self.get_property('iso'),
                'url' : self.get_property('url'),
            })
        disk.init_image()
        self.vm.set_property('bootdev', 'cdrom0')
        self.cdrom_image = disk.get_image_file()

        if mount:
            print "mouting iso ..."

    def run(self):
        self.initVM()
        self.vm.start()

class VmInstallerDebian(VmInstallerBase):
    def __init__(self, spec, vm):
        VmInstallerBase.__init__(self, spec, vm)

        # default kernel parameters
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

        # maps our properties to kernel parameters
        self.vm_kparm = {
            'hostname': 'hostname',
            'domain':   'domain',
            'locale':   'locale',
        }

        # NOTE: all the keys here need to be present for calling set() on them,
        # in order to have their type. Keys w/ None value will be omitted in
        # the final preseed file.
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
        # create preseed.cfg
        tmpdir = self.vm.get_tmpdir()
        self.write_preseed(tmpdir)

        # prepare initrd
        initrd_src = self.get_property('initrd')
        initrd_tmp = tmpdir+"/initrd"
        initrd_tmpgz = initrd_tmp+".gz"

        call(["cp", initrd_src, tmpdir+'/initrd.gz'])
        call(["gunzip", "-f", tmpdir+'/initrd.gz'])

        p = Popen(['cpio', '-H', 'newc', '-o', '-A', '-F', 'initrd'], stdout=PIPE, stdin=PIPE, stderr=STDOUT, cwd=tmpdir)
        print p.communicate(input=b'preseed.cfg\n')[0].decode()
        call(["gzip", "-f", initrd_tmp])

        self.vm.set_property('initrd', initrd_tmpgz)

    def initVM(self):
        self.prepare_cdrom()

        # kernel parameters
        self.kernel_param = KernelParam(self.get_property('kernel-args'))

        # this doesn't override explict kernel params
        for kp, kv in self.vm_kparm.iteritems():
            self.kernel_param.add(kp, self.vm.get_property(kv))

        # add default values
        self.kernel_param.add_list(self.std_kparm)

        self.vm.set_property('kernel', self.get_property('kernel'))
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
