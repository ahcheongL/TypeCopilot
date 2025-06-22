import os
from conf import Conf, load_conf
import typecopilot
import typematcher
from tabulate import tabulate
import subprocess


def run_accuracy(workspace, res_dir, groundtruth_dir, run_conf: Conf, baseline=False):
    run_conf.log(baseline)

    prog_dir = os.path.join(res_dir, run_conf.suite)
    if not os.path.exists(prog_dir):
        os.makedirs(prog_dir)

    accuracy_path = os.path.join(
        prog_dir, run_conf.program + "." + run_conf.type_src + ".accuracy"
    )

    if os.path.exists(accuracy_path):
        with open(accuracy_path, "r") as f:
            lines = f.readlines()
            total_cnt = int(lines[0].split()[-1])
            cover_cnt = int(lines[1].split()[-1])
            valid_cnt = int(lines[2].split()[-1])
    else:
        # run
        res_path = os.path.join(
            prog_dir, run_conf.program + "." + run_conf.type_src + ".txt"
        )
        typecopilot.run(
            run_conf.bc_path, res_path, workspace, run_conf.type_src, baseline
        )

        # compare accuracy
        res_map = typematcher.load_res(res_path)
        global_var_count, global_valid_count = typematcher.eval_global(
            os.path.join(groundtruth_dir, run_conf.program + ".global.csv"), res_map
        )
        local_var_count, local_valid_count = typematcher.eval_local(
            os.path.join(groundtruth_dir, run_conf.program + ".local.csv"), res_map
        )

        total_cnt = typematcher.res_map_size(res_map)
        cover_cnt = global_var_count + local_var_count
        valid_cnt = global_valid_count + local_valid_count

    if cover_cnt == 0:
        print(
            tabulate(
                [
                    [
                        total_cnt,
                        cover_cnt,
                        valid_cnt,
                    ]
                ],
                headers=["Res Size #", "Eval #", "Valid #"],
            )
        )
    else:
        print(
            tabulate(
                [
                    [
                        total_cnt,
                        cover_cnt,
                        valid_cnt,
                        round(valid_cnt / cover_cnt * 100, 2),
                    ]
                ],
                headers=["Res Size #", "Eval #", "Valid #", "Acc."],
            )
        )

    with open(accuracy_path, "w") as f:
        f.write("total_cnt: %d\n" % total_cnt)
        f.write("cover_cnt: %d\n" % cover_cnt)
        f.write("valid_cnt: %d\n" % valid_cnt)


# main entry
if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")
    baseline_dir = os.path.join(workspace, "data-baseline")
    groundtruth_dir = os.path.join(workspace, "groundtruth")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    confs = load_conf("conf.yaml")
    for conf in confs:
        for type_src in ["mig", "di", "comb"]:
            conf.type_src = type_src
            # baseline
            run_accuracy(
                workspace,
                baseline_dir,
                os.path.join(groundtruth_dir, conf.suite),
                conf,
                True,
            )

            # result
            run_accuracy(
                workspace,
                typecopilot_dir,
                os.path.join(groundtruth_dir, conf.suite),
                conf,
            )
