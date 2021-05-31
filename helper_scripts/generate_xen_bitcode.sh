#!/bin/sh
rm -r llvm_codestore
mkdir llvm_codestore
PATH=$PATH:/home/styxs/uni/systems_hardening/difuze/helper_scripts/post_processing/ python2 run_all.py -skp -skP -ske -ski -skI -skv -skd -g clang -clangp /bin/clang -n 2 -o /home/styxs/uni/systems_hardening/xen/test_output -m /home/styxs/uni/systems_hardening/xen/makeout.txt -f ioctl_cmd_finder_out -l llvm_codestore -k ~/uni/systems_hardening/difuze/xen -a 5
