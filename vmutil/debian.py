from util import get_opt
from kernelparam import KernelParam
from vmconfigdisk import VmConfigDisk
from subprocess import call
from subprocess import Popen, PIPE, STDOUT

class DebianPreseed(object):
    def __init__(self, fn):
        self.fn = fn
        self.fp = open(fn, 'w+')

    def add_text(self, txt):
        for l in txt:
            self.fp.write(l+"\n")

    def _add(self, cat, name, t, value, dflt = None):
        if value is None:
            value = dflt
        if value is not None:
            self.add_text([cat+" "+name+" "+t+" "+value])

    def di_str(self, name, value, dflt = None):
        self._add("d-i", name, "string", value, dflt)

    def di_str_list(self, lst):
        for pn, pv in lst.iteritems():
            self.di_str(pn, pv)

    def di_flag_list(self, lst):
        for pn, pv in lst.iteritems():
            if pv:
                self._add('d-i', pn, 'boolean', 'true')
            else:
                self._add('d-i', pn, 'boolean', 'false')

    def finish(self):
        self.fp.close()

class VmInstallerBase(object):
    def __init__(self, spec, vm):
        self.spec = spec
        self.vm = vm

    def get_property(self, pr):
        return get_opt(self.spec, pr)

    def run(self):
        self.initVM()
        self.vm.start()

class VmInstallerDebian(VmInstallerBase):
    def __init__(self, spec, vm):
        VmInstallerBase.__init__(self, spec, vm)
        self.std_kparm = {
            'vga':                                          'normal',
            'fb':                                           'false',
            'recommends':                                   'false',
            'modules':                                      'openssh-client-udeb',
            'DEBIAN_FRONTEND':                              'text',
        }

        self.vm_kparm = {
            'hostname':               'hostname',
            'domain':                 'domain',
            'locale':                 'locale',
            'keymap':                 'keymap',
            'clock-setup/ntp-server': 'ntp-server',
        }

        self.preseed_text = [
            'popularity-contest popularity-contest/participate boolean false',
            'd-i base-installer/install-recommends boolean false',
            'tasksel tasksel/first multiselect minimal, ssh-server',

            # apt mirror
            'apt-mirror-setup apt-setup/use_mirror            boolean   true',
            'apt-mirror-setup apt-setup/cdrom/set-first       boolean   false',
            'apt-mirror-setup apt-setup/cdrom/set-next        boolean   false',
            'apt-mirror-setup apt-setup/cdrom/set-failed      boolean   false',
            'd-i mirror/country                               string    de',
#            'd-i mirror/http/hostname                         string    http://ftp.gwdg.de/pub/linux/debian/',
#            'd-i mirror/http/directory                        string    /debian',
            'd-i mirror/http/proxy                            string',

#            'd-i mirror/http/hostname                         string    auto.mirror.devuan.org',
#            'd-i mirror/http/directory                        string    /merged',

            # hw-detect trimdown
#            'd-i hw-detect/load_firmware                      boolean   false',
#            'd-i hw-detect/start_pcmcia                       boolean   false',

            # initial user/pw
            'd-i passwd/root-login                            boolean   true',
            'd-i passwd/make-user                             boolean   true',
            'd-i passwd/root-password                         password  Mot2p@ss',
            'd-i passwd/root-password-again                   password  Mot2p@ss',
            'd-i passwd/user-fullname                         string    adminit',
            'd-i passwd/username                              string    adminit',
            'd-i passwd/user-password                         password  Mot2p@ss',
            'd-i passwd/user-password-again                   password  Mot2p@ss',

            # automatic partitioning
            'd-i partman-auto/init_automatically_partition    select    biggest_free',
            'd-i partman-auto/disk                            string    /dev/sda',
            'd-i partman-auto/choose_recipe                   select    atomic',
            'd-i partman-auto/method                          string    regular',
            'd-i partman-partitioning/confirm_write_new_label boolean   true',
            'd-i partman/choose_partition                     select    finish',
            'd-i partman/confirm                              boolean   true',
            'd-i partman/confirm_nooverwrite                  boolean   true',

            # bootloader
            'd-i clock-setup/utc                              boolean   true',
            'd-i grub-installer/skip                          boolean   false',
            'd-i grub-installer/only_debian                   boolean   true',
            'd-i grub-installer/bootdev                       string    default',

            # automatic poweroff
            'd-i debian-installer/exit/poweroff               boolean   true',
        ]

        self.preseed_di_flags = {
            'debian-installer/exit/poweroff': True,
            'clock-setup/utc':                True,
            'hw-detect/load_firmware':        False,
            'hw-detect/start_pcmcia':         False,
        }

    def write_preseed(self, tmpdir):
        call(['mkdir', '-p', tmpdir])

        preseed = DebianPreseed(tmpdir+'/preseed.cfg')
        preseed.add_text(self.preseed_text)
        preseed.di_flag_list(self.preseed_di_flags)
        preseed.di_str_list({
            'time/zone':             self.vm.get_property('timezone'),
            'mirror/http/directory': self.get_property('mirror-http-directory'),
            'mirror/http/hostname':  self.get_property('mirror-http-hostname'),
        })
        preseed.finish()

    def prepare_initrd(self):
        # create preseed.cfg
        tmpdir = 'tmp'
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
        # add the boot cdrom
        dsk = {
            'type': 'iso-image',
            'name': 'cdrom0',
            'file': self.spec['iso']
        }
        self.vm.add_disk(VmConfigDisk(dsk, self.vm))
        self.vm.set_property('bootdev', 'cdrom0')

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
