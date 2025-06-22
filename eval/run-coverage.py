import os
import subprocess
from conf import Conf, load_conf
import typecopilot
from copy import deepcopy


def run_coverage(workspace, target_dir, run_conf: Conf, baseline=False):
    run_conf.log(baseline)

    prog_dir = os.path.join(target_dir, run_conf.suite)
    if not os.path.exists(prog_dir):
        os.makedirs(prog_dir)

    res_path = os.path.join(
        prog_dir, run_conf.program + "." + run_conf.type_src + ".coverage"
    )
    typecopilot.coverage(
        run_conf.bc_path, res_path, workspace, run_conf.type_src, baseline
    )

    with open(res_path, "r") as f:
        lines = f.readlines()
        print(lines[2])


"""
This script is to check which variable is not covered in typecopilot results.
"""
if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")
    baseline_dir = os.path.join(workspace, "data-baseline")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    confs = load_conf("conf.yaml")
    for conf in confs:
        for type_src in ["mig", "di", "comb"]:
            conf.type_src = type_src

            # baseline
            run_coverage(
                workspace,
                baseline_dir,
                conf,
                True,
            )

            # result
            run_coverage(
                workspace,
                typecopilot_dir,
                conf,
            )
