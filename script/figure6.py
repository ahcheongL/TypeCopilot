import os
import subprocess
from conf import Conf, load_conf
import coreutils
from tabulate import tabulate, SEPARATING_LINE
import typecopilot
import typematcher
from table3 import codeql_accuracy, coverage

legend_map = {
    "mig": "Residual Types (Baseline)",
    "di": "Debug Information",
    "comb": "TypeCopilot",
}

subfigure_counter = 0


# main driver for AE CodeQL
def ae_accuracy(workspace, typecopilot_dir, baseline_dir, groundtruth_dir):
    table_data = []
    # handle coreutils
    coreutils_conf = load_conf("coreutils.yaml")
    for type_src in ["mig", "di", "comb"]:
        wo_cover_cnt = 0
        wo_valid_cnt = 0
        w_cover_cnt = 0
        w_valid_cnt = 0

        for conf in coreutils_conf:
            conf.type_src = type_src
            __cover_cnt, __valid_cnt = codeql_accuracy(
                workspace, baseline_dir, os.path.join(groundtruth_dir, "coreutils"), conf, True
            )
            wo_cover_cnt += __cover_cnt
            wo_valid_cnt += __valid_cnt

            __cover_cnt, __valid_cnt = codeql_accuracy(
                workspace, typecopilot_dir, os.path.join(groundtruth_dir, "coreutils"), conf, False
            )
            w_cover_cnt += __cover_cnt
            w_valid_cnt += __valid_cnt

        table_data.append(
            [
                legend_map[type_src],
                str(round(wo_valid_cnt / wo_cover_cnt * 100, 2)) + "%",
                str(round(w_valid_cnt / w_cover_cnt * 100, 2)) + "%",
            ]
        )
    global subfigure_counter
    print(f"\n({chr(97 + subfigure_counter)}) Accuracy: Coreutils")
    print(
        tabulate(table_data, headers=["Type Source", "w/o TypeInfer", "w/ TypeInfer"])
    )
    subfigure_counter += 1

    # handle other programs
    confs = load_conf("conf.yaml")
    for conf in confs:
        table_data = []
        for type_src in ["mig", "di", "comb"]:
            conf.type_src = type_src
            wo_cover_cnt, wo_valid_cnt = codeql_accuracy(
                workspace, baseline_dir, os.path.join(groundtruth_dir, conf.suite), conf, True
            )

            w_cover_cnt, w_valid_cnt = codeql_accuracy(
                workspace, typecopilot_dir, os.path.join(groundtruth_dir, conf.suite), conf, False
            )

            table_data.append(
                [
                    legend_map[type_src],
                    str(round(wo_valid_cnt / wo_cover_cnt * 100, 2)) + "%",
                    str(round(w_valid_cnt / w_cover_cnt * 100, 2)) + "%",
                ]
            )

        print(f"\n({chr(97 + subfigure_counter)}) Accuracy: {conf.suite}")
        print(
            tabulate(table_data, headers=["Type Source", "w/o TypeInfer", "w/ TypeInfer"])
        )
        subfigure_counter += 1


def ae_coverage(workspace, typecopilot_dir, baseline_dir):
    global subfigure_counter

    # handle coreutils
    table_data = []
    coreutils_conf = load_conf("coreutils.yaml")
    for type_src in ["mig", "di", "comb"]:
        wo_total_cnt = 0
        wo_cover_cnt = 0
        w_total_cnt = 0
        w_cover_cnt = 0

        for conf in coreutils_conf:
            conf.type_src = type_src
            total_cnt, cover_cnt = coverage(workspace, baseline_dir, conf, True)
            wo_total_cnt += total_cnt
            wo_cover_cnt += cover_cnt

            total_cnt, cover_cnt = coverage(workspace, typecopilot_dir, conf, False)
            w_total_cnt += total_cnt
            w_cover_cnt += cover_cnt

        table_data.append(
            [
                legend_map[type_src],
                str(round(wo_cover_cnt / wo_total_cnt * 100, 2)) + "%",
                str(round(w_cover_cnt / w_total_cnt * 100, 2)) + "%",
            ]
        )
    print(f"\n({chr(97 + subfigure_counter)}) Coverage: Coreutils")
    print(
        tabulate(table_data, headers=["Type Source", "w/o TypeInfer", "w/ TypeInfer"])
    )
    subfigure_counter += 1

    # handle other programs
    confs = load_conf("conf.yaml")
    for conf in confs:
        table_data = []
        for type_src in ["mig", "di", "comb"]:
            conf.type_src = type_src
            wo_total_cnt, wo_cover_cnt = coverage(workspace, baseline_dir, conf, True)
            w_total_cnt, w_cover_cnt = coverage(workspace, typecopilot_dir, conf, False)

            table_data.append(
                [
                    legend_map[type_src],
                    str(round(wo_cover_cnt / wo_total_cnt * 100, 2)) + "%",
                    str(round(w_cover_cnt / w_total_cnt * 100, 2)) + "%",
                ]
            )

        print(f"\n({chr(97 + subfigure_counter)}) Coverage: {conf.suite}")
        print(
            tabulate(table_data, headers=["Type Source", "w/o TypeInfer", "w/ TypeInfer"])
        )
        subfigure_counter += 1

if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")
    baseline_dir = os.path.join(workspace, "data-baseline")
    groundtruth_dir = os.path.join(workspace, "groundtruth")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    ae_accuracy(workspace, typecopilot_dir, baseline_dir, groundtruth_dir)
    ae_coverage(workspace, typecopilot_dir, baseline_dir)
