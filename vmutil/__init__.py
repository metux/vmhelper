import kernelparam
import cmdline
import vmqemu
import util
import vminstaller
import vmconfig
import globalconf
import gz

#KernelParam      = kernelparam.KernelParam
#CmdLine          = cmdline.CmdLine
#parse_size       = util.parse_size
#init_sparse_file = util.init_sparse_file
#get_opt_bool     = util.get_opt_bool
#get_opt          = util.get_opt
#flatten          = util.flatten
#VmQemu           = vmqemu.VmQemu
VmConfig         = vmconfig.VmConfig
#getInstaller     = vminstaller.getInstaller
GlobalConfig     = globalconf.GlobalConfig

def mkdir(dn):
    if dn is None:
        print "mkdir called w/ none"
    call(["mkdir", "-p", dn])
