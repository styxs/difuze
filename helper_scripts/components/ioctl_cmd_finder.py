from base_component import *
import os
import argparse
from multiprocessing import Pool, cpu_count
import tempfile

PARAMETER_DESCRIPTION = {
    'do_dm_op' : (1, None),
    'do_set_timer_op' : (-1, -1), # if else
    'do_event_channel_op_compat' : (None, None), # cmd inside parameter struct
    'do_xenoprof_op' : (0, 1),
    'do_vm_assist' : (0, -1),
    'do_update_va_mapping_otherdomain' : (-1, -1), # No cmd parameter
    'do_platform_op' : (None, None), # cmd inside parameter struct
    'do_xenpmu_op' : (0, None),
    'do_set_callbacks' : (None, None), # No cmd or arg parameter
    'do_hvm_op' : (0, None),
    'do_stack_switch' : (None, None), # No cmd or arg parameter
    'do_flask_op' : (None, None), # cmd inside parameter struct
    'do_fpu_taskswitch' : (None, None), # No cmd or arg parameter
    'do_hypfs_op' : (0, None),
    'do_get_debugreg' : (None, None), # No cmd or arg parameter
    'do_set_debugreg' : (None, None), # No cmd or arg parameter
    'do_argo_op' : (0, None),
    'do_set_segment_base' : (0, None),
    'do_mca' : (None, None), # cmd inside parameter struct
    'do_callback_op' : (0, None), # cmd inside parameter struct
    'do_update_va_mapping' : (None, None), # No cmd or arg parameter (or modified with bitwise &)
    'do_sysctl' : (None, None), # cmd inside parameter struct
    'do_kexec_op' : (0, None),
    'do_iret' : (None, None), # no parameters
    'do_kexec_op_internal' : (0, None), # no parameters
    'do_update_descriptor' : (None, None), # No cmd or arg parameter
    'do_physdev_op' : (0, None),
    'do_sched_op' : (0, None),
    'do_set_gdt' : (None, None), # No cmd or arg parameter
    'do_sched_op_compat' : (0, 1),
    'do_console_io' : (0, None),
    'do_domctl' : (None, None), # Arch specific or no cmd or arg parameter
    'do_physdev_op_compat' : (None, None), # No cmd or arg parameter
    'do_event_channel_op' : (0, None),
    'do_set_trap_table' : (None, None), # No cmd or arg parameter
    'do_vmtrace_op' : (None, None), # cmd inside parameter struct
    'do_vcpu_op' : (0, None),
    'do_altp2m_op' : (None, None), # cmd inside parameter struct
    'do_nmi_op' : (0, None),
    'do_grant_table_op' : (0, None),
}

class IoctlCmdFinder(Component):
    """
        Component which tries to find all ioctl commands and their corresponding structure.
    """

    def __init__(self, value_dict):
        ioctl_finder_so = None
        entry_point_out = None
        ioctl_finder_out = None
        opt_bin_path = None
        llvm_bc_out = ""
        kernel_src_dir = ""
        if 'ioctl_finder_so' in value_dict:
            ioctl_finder_so = value_dict['ioctl_finder_so']
        if 'entry_point_out' in value_dict:
            entry_point_out = value_dict['entry_point_out']
        if 'ioctl_finder_out' in value_dict:
            ioctl_finder_out = value_dict['ioctl_finder_out']
        if 'opt_bin_path' in value_dict:
            opt_bin_path = value_dict['opt_bin_path']
        if 'llvm_bc_out' in value_dict:
            llvm_bc_out = value_dict["llvm_bc_out"]
        if 'kernel_src_dir' in value_dict:
            kernel_src_dir = value_dict["kernel_src_dir"]

        self.opt_bin_path = opt_bin_path
        self.ioctl_finder_so = ioctl_finder_so
        self.entry_point_out = entry_point_out
        self.ioctl_finder_out = ioctl_finder_out
        self.llvm_bc_out = llvm_bc_out
        self.kernel_src_dir = kernel_src_dir

    def setup(self):
        if not os.path.exists(self.ioctl_finder_so):
            return "Provided ioctl finder so path:" + str(self.ioctl_finder_so) + " does not exist."
        if not os.path.exists(self.opt_bin_path):
            return "Provided opt bin path:" + str(self.opt_bin_path) + " does not exist."
        if not os.path.exists(self.entry_point_out):
            return "Provided entry point out file path:" + str(self.entry_point_out) + " is invalid."
        if self.ioctl_finder_out is None:
            return "Provided ioctl cmd finder out file path:" + str(self.ioctl_finder_out) + " is invalid."
        # set up the directory if this is not present.
        if not os.path.isdir(self.ioctl_finder_out):
            os.system('mkdir -p ' + self.ioctl_finder_out)

        return None

    def perform(self):
        log_info("Invoking Ioctl cmd finder")
        return _run_ioctl_cmd_finder(self.entry_point_out, self.opt_bin_path, self.ioctl_finder_so,
                                     self.ioctl_finder_out, self.llvm_bc_out, self.kernel_src_dir)

    def get_name(self):
        return "IoctlCmdFinder"

    def is_critical(self):
        # Yes, this component is critical.
        return True


def setup_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', action='store', dest='entry_point_out',
                        help='Path to the entry point output file.')

    parser.add_argument('-p', action='store', dest='opt_bin_path',
                        help='Path to the opt executable.')

    parser.add_argument('-s', action='store', dest='ioctl_finder_so',
                        help='Path to the IoctlFinder shared object (so).')

    parser.add_argument('-f', action='store', dest='ioctl_finder_out',
                        help='Path to the output folder where the ioctl command finder output should be stored.')

    return parser


def main():
    arg_parser = setup_args()
    parsed_args = arg_parser.parse_args()
    arg_dict = dict()
    arg_dict['opt_bin_path'] = parsed_args.opt_bin_path
    arg_dict['ioctl_finder_so'] = parsed_args.ioctl_finder_so
    arg_dict['ioctl_finder_out'] = parsed_args.ioctl_finder_out
    arg_dict['entry_point_out'] = parsed_args.entry_point_out
    ioctl_comp_out = IoctlCmdFinder(arg_dict)
    setup_msg = ioctl_comp_out.setup()
    if setup_msg is not None:
        log_error("Component:", ioctl_comp_out.get_name(), " setup failed with msg:", setup_msg)
    else:
        perf_out = ioctl_comp_out


def _run_ioctl_cmd_parser(combined_arg):

    opt_bin_path = combined_arg[0]
    so_path = combined_arg[1]
    func_name = combined_arg[2]
    if func_name in ["do_memory_op", "do_mmuext_op", "do_mmu_update", "do_multicall"]:
        log_warning("Ioctl cmd finder skipped for:" + func_name)
        return 1, func_name
    llvm_bc_file = combined_arg[3]
    output_file = combined_arg[4]
    llvm_bc_out = combined_arg[5]
    kernel_src_dir = combined_arg[6]
    temp_bc_file = tempfile.NamedTemporaryFile(delete=False)
    bc_file_name = temp_bc_file.name
    temp_bc_file.close()

    cmdParamPos, argParamPos = PARAMETER_DESCRIPTION.get(func_name, (-2, -2))
    if cmdParamPos is -2 and argParamPos is -2:
        print("No parameter description for ", func_name)
        return 1, func_name
    if cmdParamPos is None and argParamPos is None:
        print("Skipping because of no valid params: ", func_name)
        return 1, func_name
    if cmdParamPos is None:
        cmdParamPos = -1
    if argParamPos is None:
        argParamPos = -1
    #print("Running on:", opt_bin_path, so_path, func_name, llvm_bc_file, output_file, llvm_bc_out)
    # run mem2reg
    ret_val = os.system(opt_bin_path + " -mem2reg " + llvm_bc_file + " -o " + bc_file_name)
    if ret_val != 0:
        log_error("LLVM mem2reg failed on:", llvm_bc_file, " for function:", func_name,
                  ", So the output you get may be wrong.")

    # Old ioctl cmd parser
    '''ret_val = os.system(opt_bin_path + " -analyze -debug -load " + so_path + ' -ioctl-cmd-parser -toCheckFunction=\"' +
                        str(func_name) + '\" ' + bc_file_name + ' > ' + output_file + ' 2>&1')'''
    #print("Running ioctl parser now on: ", llvm_bc_file)
    print("STARTING: {}".format(str(func_name)))
    ret_val = os.system(opt_bin_path + " -analyze -load " + so_path + ' -new-ioctl-cmd-parser -ioctlFunction=\"' +
                        str(func_name) + '\" -bcOutDir=\"' + llvm_bc_out + '\" -srcBaseDir=\"' + kernel_src_dir + '\" -cmdParamPos=\"' + str(cmdParamPos) + '\" -argParamPos=\"' + str(argParamPos) + '\" ' +
                        bc_file_name + ' >> ' + output_file + ' 2>&1')
    print("SUCCESSFULLY FINISHED: {}".format(str(func_name)))
    #print("Got the ioctl parser ret_val:", ret_val, "for:", llvm_bc_file)
    return ret_val, func_name


def _get_file_to_write(func_name, output_folder):
    output_file = os.path.join(output_folder, func_name + '.txt')
    func_num = 1
    while os.path.exists(output_file):
        output_file = os.path.join(output_folder, func_name + '_' + str(func_num) + '.txt')
        func_num += 1
    return output_file


def _run_ioctl_cmd_finder(entry_point_out, opt_bin_path, ioctl_so_path, ioctl_finder_out, llvm_bc_out, kernel_src_dir):
    to_run_cmds = []
    fp = open(entry_point_out, 'r')
    all_lines = fp.readlines()
    fp.close()
    processed_func = []
    for curr_ep in all_lines:
        curr_ep = curr_ep.strip()
        all_p = curr_ep.split(':')
        if all_p[0] == 'XENHYPERCALL' and (all_p[1] + all_p[2]) not in processed_func:
            processed_func.append(all_p[1] + all_p[2])
            to_run_cmds.append((opt_bin_path, ioctl_so_path, all_p[1], all_p[-1],
                                os.path.join(ioctl_finder_out, all_p[3]), llvm_bc_out, kernel_src_dir))

    log_info("Found:", len(to_run_cmds), " ioctl functions to process.")
    log_info("Processing in multiprocessing mode")
    p = Pool(cpu_count())
    #p = Pool(1)
    return_vals = p.map(_run_ioctl_cmd_parser, to_run_cmds)
    log_info("Finished processing:", len(to_run_cmds), " ioctl functions.")
    total_failed = 0
    for curr_r_val in return_vals:
        if int(curr_r_val[0]) != 0:
            total_failed += 1
            log_error("Ioctl cmd finder failed for:", curr_r_val[-1])
    log_info("Ioctl Cmd finder failed for:", total_failed, " out of:", len(to_run_cmds), " Ioctl functions.")
    return True


if __name__ == "__main__":
    main()
