from util import get_opt
from kernelparam import KernelParam
from vmconfigdisk import VmConfigDisk
from subprocess import call
from subprocess import Popen, PIPE, STDOUT
from debian import DebianPreseed

class VmInstallerBase(object):
    def __init__(self, spec, vm):
        self.spec = spec
        self.vm = vm

    def get_property(self, pr):
        return get_opt(self.spec, pr)

    """Prepare the installer cdrom image. optionally mount it"""
    def prepare_cdrom(self, mount=False):
        # add the boot cdrom
        dsk = {
            'type': 'iso-image',
            'name': 'cdrom0',
            'file': self.spec['iso']
        }
        self.vm.add_disk(VmConfigDisk(dsk, self.vm))
        self.vm.set_property('bootdev', 'cdrom0')
        self.cdrom_image = self.spec['iso']

    def run(self):
        self.initVM()
        self.vm.start()

class VmInstallerDebian(VmInstallerBase):
    def __init__(self, spec, vm):
        VmInstallerBase.__init__(self, spec, vm)
        self.std_kparm = {
            'vga':              'normal',
            'fb':               'false',
            'recommends':       'false',
            'modules':          'openssh-client-udeb',
            'DEBIAN_FRONTEND':  'text',
        }

        self.vm_kparm = {
            'hostname':               'hostname',
            'domain':                 'domain',
            'locale':                 'locale',
#            'clock-setup/ntp-server': 'ntp-server',
        }

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

                # initial user/pw
                'passwd/root-login':                            [ 'boolean',     'true'                ],
                'passwd/make-user':                             [ 'boolean',     'true'                ],
                'passwd/root-password':                         [ 'password',    'knollo123'           ],
                'passwd/root-password-again':                   [ 'password',    'knollo123'           ],
                'passwd/user-fullname':                         [ 'string',      'adminit'             ],
                'passwd/username':                              [ 'string',      'adminit'             ],
                'passwd/user-password':                         [ 'password',    'knollo123'           ],
                'passwd/user-password-again':                   [ 'password',    'knollo123'           ],

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
        pr = DebianPreseed(tmpdir+'/preseed.cfg', self.preseed_list)

        pr.set_timezone(self.get_property('timezone'))
        pr.set_http_mirror(self.get_property('deb/mirror/http/hostname'), self.get_property('deb/mirror/http/directory'))
        pr.set_keymap(self.get_property('deb/keyboard/layout'))

        pr.finish()

    def prepare_initrd(self):
        # create preseed.cfg
        tmpdir = 'tmp'
        call(['mkdir', '-p', tmpdir])

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
