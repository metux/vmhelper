from subprocess import call
from cmdline import CmdLine

class VmQemu:
    def __init__(self, vm):
        self.vm = vm

    def get_qemu_args(self):
        cmd = CmdLine("qemu-system-"+self.vm.get_property('arch'))
        cmd.opt_arg('-boot',      self.get_bootdev())
        cmd.opt_arg('-cdrom',     self.vm.get_disk_file('cdrom0'))
        cmd.opt_arg('-hda',       self.vm.get_disk_file('disk0'))
        cmd.opt_arg('-m',         self.vm.get_property('memory'))
        cmd.opt_arg('-kernel',    self.vm.get_property('kernel'))
        cmd.opt_arg('-initrd',    self.vm.get_property('initrd'))
        cmd.opt_arg('-append',    self.vm.get_property('append'))
        cmd.opt_arg('-dtb',       self.vm.get_property('dtb'))
        cmd.opt_arg('-k',         self.vm.get_property('keymap'))
        cmd.opt_sw('-enable-kvm', self.vm.get_property_bool('kvm'))

        print "keymap:"+self.vm.get_property('keymap')

        return cmd.args

    def get_bootdev(self):
        bd = self.vm.get_property('bootdev')
        if bd == 'disk0':
            return 'c'
        if bd == 'cdrom' or bd == 'cdrom0':
            return 'once=d'
        return None

    def start(self):
        qemu_args = self.get_qemu_args()
        call(qemu_args)
