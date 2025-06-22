import os
import subprocess
from copy import deepcopy
from conf import Conf, load_conf


# get the number of variables and covered
def get_cnt(target_dir, run_conf: Conf):
    prog_dir = os.path.join(target_dir, run_conf.suite)

    res_path = os.path.join(
        prog_dir, run_conf.program + "." + run_conf.type_src + ".coverage"
    )

    with open(res_path, "r") as f:
        lines = f.readlines()

        # calculate the total number of pointers
        var_cnt = int(lines[0].split()[-1])
        cover_cnt = int(lines[1].split()[-1])

        return var_cnt, cover_cnt


"""
This script is used to evaluate the coverage of the opaque pointer.
"""
if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")
    baseline_dir = os.path.join(workspace, "data-baseline")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    confs = load_conf("conf.yaml")
    for conf in confs:
        conf.type_src = "mig"

        # get count of pointers
        var_cnt, baseline_cover_cnt = get_cnt(baseline_dir, conf)
        ptr_cnt = var_cnt - baseline_cover_cnt

        # get count of inferred pointers
        conf.type_src = "comb"
        var_cnt, typecopilot_cover_cnt = get_cnt(typecopilot_dir, conf)
        inferred_cnt = typecopilot_cover_cnt - baseline_cover_cnt

        print(conf.suite)
        print("total ptr coverage: %.2f%%\n" % round(inferred_cnt / ptr_cnt * 100, 2))
