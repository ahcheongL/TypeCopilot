import os
import subprocess
from conf import Conf, load_conf
import coreutils
from tabulate import tabulate, SEPARATING_LINE
import typecopilot
import typematcher


def coverage(workspace, target_dir, run_conf: Conf, baseline=False):
    prog_dir = os.path.join(target_dir, run_conf.suite)
    if not os.path.exists(prog_dir):
        os.makedirs(prog_dir)

    res_path = os.path.join(
        prog_dir, run_conf.program + "." + run_conf.type_src + ".coverage"
    )
    typecopilot.coverage(
        run_conf.bc_path,
        res_path,
        workspace,
        run_conf.type_src,
        baseline,
        run_conf.worklist,
    )

    with open(res_path, "r") as f:
        lines = f.readlines()
        total_cnt = int(lines[0].split()[-1])
        cover_cnt = int(lines[1].split()[-1])
        return total_cnt, cover_cnt


def codeql_accuracy(
    workspace, res_dir, groundtruth_dir, run_conf: Conf, baseline=False
):
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
            run_conf.bc_path,
            res_path,
            workspace,
            run_conf.type_src,
            baseline,
            run_conf.worklist,
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

        with open(accuracy_path, "w") as f:
            f.write("total_cnt: %d\n" % total_cnt)
            f.write("cover_cnt: %d\n" % cover_cnt)
            f.write("valid_cnt: %d\n" % valid_cnt)

    return cover_cnt, valid_cnt


def tbaa_accuracy(workspace, res_dir, conf: Conf, baseline=False):
    prog_dir = os.path.join(res_dir, conf.suite)
    if not os.path.exists(prog_dir):
        os.makedirs(prog_dir)

    tbaa_accuracy_path = os.path.join(
        prog_dir, conf.program + "." + conf.type_src + ".tbaa"
    )

    if os.path.exists(tbaa_accuracy_path):
        with open(tbaa_accuracy_path, "r") as f:
            lines = f.readlines()
            total_cnt = int(lines[0].split(": ")[1])
            valid_cnt = int(lines[1].split(": ")[1])
    else:
        # run
        cmd = (
            f"make tbaa BC={conf.bc_path} TYPE_SRC={conf.type_src} BASELINE={baseline} WL={conf.worklist}"
        )
        process = subprocess.Popen(
            cmd,
            cwd=workspace,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = process.communicate()
        with open(tbaa_accuracy_path, "w") as f:
            f.write(stderr.decode("utf-8"))
        res = stderr.decode("utf-8").split("\n")

        total_cnt = res[0].split(": ")[1]
        valid_cnt = res[1].split(": ")[1]

    return int(total_cnt), int(valid_cnt)


# main driver for AE Coverage
def ae_coverage(workspace, typecopilot_dir, baseline_dir):
    coverage_baseline_map = {}
    coverage_typecopilot_map = {}
    coverage_increase_map = {}

    # handle coreutils
    coreutils_conf = load_conf("coreutils.yaml")
    baseline_total_cnt = 0
    baseline_cover_cnt = 0
    typecopilot_total_cnt = 0
    typecopilot_cover_cnt = 0

    for conf in coreutils_conf:
        # baseline
        conf.type_src = "mig"
        total_cnt, cover_cnt = coverage(workspace, baseline_dir, conf, True)
        baseline_total_cnt += total_cnt
        baseline_cover_cnt += cover_cnt

        # result
        conf.type_src = "comb"
        total_cnt, cover_cnt = coverage(workspace, typecopilot_dir, conf, False)
        typecopilot_total_cnt += total_cnt
        typecopilot_cover_cnt += cover_cnt

    coverage_baseline_map["coreutils"] = round(
        baseline_cover_cnt / baseline_total_cnt * 100, 2
    )
    coverage_typecopilot_map["coreutils"] = round(
        typecopilot_cover_cnt / typecopilot_total_cnt * 100, 2
    )
    coverage_increase_map["coreutils"] = round(
        100
        * (
            typecopilot_cover_cnt / typecopilot_total_cnt
            - baseline_cover_cnt / baseline_total_cnt
        ),
        2,
    )

    # handle other programs
    confs = load_conf("conf.yaml")
    for conf in confs:
        # baseline
        conf.type_src = "mig"
        total_cnt, cover_cnt = coverage(workspace, baseline_dir, conf, True)
        baseline_total_cnt += total_cnt
        baseline_cover_cnt += cover_cnt
        coverage_baseline_map[conf.suite] = round(
            baseline_cover_cnt / baseline_total_cnt * 100, 2
        )

        # result
        conf.type_src = "comb"
        total_cnt, cover_cnt = coverage(workspace, typecopilot_dir, conf, False)
        typecopilot_total_cnt += total_cnt
        typecopilot_cover_cnt += cover_cnt

        coverage_typecopilot_map[conf.suite] = round(
            typecopilot_cover_cnt / typecopilot_total_cnt * 100, 2
        )
        coverage_increase_map[conf.suite] = round(
            100
            * (
                typecopilot_cover_cnt / typecopilot_total_cnt
                - baseline_cover_cnt / baseline_total_cnt
            ),
            2,
        )

    return coverage_baseline_map, coverage_typecopilot_map, coverage_increase_map


# main driver for AE TBAA
def ae_tbaa(workspace, typecopilot_dir, baseline_dir):
    tbaa_baseline_map = {}
    tbaa_typecopilot_map = {}
    tbaa_increase_map = {}

    # handle coreutils
    coreutils_conf = load_conf("coreutils.yaml")
    for conf in coreutils_conf:
        # baseline
        conf.type_src = "mig"
        tbaa_accuracy(workspace, baseline_dir, conf, True)

        # result
        conf.type_src = "comb"
        tbaa_accuracy(workspace, typecopilot_dir, conf, False)

    __total_cnt, __valid_cnt, total_cnt, valid_cnt = coreutils.count_tbaa_accuracy(
        os.path.join(typecopilot_dir, "coreutils"),
        os.path.join(baseline_dir, "coreutils"),
    )

    tbaa_baseline_map["coreutils"] = round(__valid_cnt / __total_cnt * 100, 2)
    tbaa_typecopilot_map["coreutils"] = round(valid_cnt / total_cnt * 100, 2)
    tbaa_increase_map["coreutils"] = round(
        100 * (valid_cnt / total_cnt - __valid_cnt / __total_cnt), 2
    )

    # handle other programs
    confs = load_conf("conf.yaml")
    for conf in confs:
        # baseline
        conf.type_src = "mig"
        __total_cnt, __valid_cnt = tbaa_accuracy(workspace, baseline_dir, conf, True)
        tbaa_baseline_map[conf.suite] = round(__valid_cnt / __total_cnt * 100, 2)

        # result
        conf.type_src = "comb"
        total_cnt, valid_cnt = tbaa_accuracy(workspace, typecopilot_dir, conf, False)
        tbaa_typecopilot_map[conf.suite] = round(valid_cnt / total_cnt * 100, 2)
        tbaa_increase_map[conf.suite] = round(
            100 * (valid_cnt / total_cnt - __valid_cnt / __total_cnt), 2
        )

    return tbaa_baseline_map, tbaa_typecopilot_map, tbaa_increase_map


# main driver for AE CodeQL
def ae_codeql(workspace, typecopilot_dir, baseline_dir, groundtruth_dir):
    codeql_baseline_map = {}
    codeql_typecopilot_map = {}
    codeql_increase_map = {}

    # handle coreutils
    coreutils_conf = load_conf("coreutils.yaml")
    baseline_cover_cnt = 0
    baseline_valid_cnt = 0
    typecopilot_cover_cnt = 0
    typecopilot_valid_cnt = 0
    for conf in coreutils_conf:
        # baseline
        conf.type_src = "mig"
        __cover_cnt, __valid_cnt = codeql_accuracy(
            workspace, baseline_dir, os.path.join(groundtruth_dir, "coreutils"), conf, True
        )
        baseline_cover_cnt += __cover_cnt
        baseline_valid_cnt += __valid_cnt

        # result
        conf.type_src = "comb"
        __cover_cnt, __valid_cnt = codeql_accuracy(
            workspace, typecopilot_dir, os.path.join(groundtruth_dir, "coreutils"), conf, False
        )
        typecopilot_cover_cnt += __cover_cnt
        typecopilot_valid_cnt += __valid_cnt

    codeql_baseline_map["coreutils"] = round(
        baseline_valid_cnt / baseline_cover_cnt * 100, 2
    )
    codeql_typecopilot_map["coreutils"] = round(
        typecopilot_valid_cnt / typecopilot_cover_cnt * 100, 2
    )
    codeql_increase_map["coreutils"] = round(
        100
        * (
            typecopilot_valid_cnt / typecopilot_cover_cnt
            - baseline_valid_cnt / baseline_cover_cnt
        ),
        2,
    )

    # handle other programs
    confs = load_conf("conf.yaml")
    for conf in confs:
        # baseline
        conf.type_src = "mig"
        __cover_cnt, __valid_cnt = codeql_accuracy(
            workspace, baseline_dir, os.path.join(groundtruth_dir, conf.suite), conf, True
        )
        codeql_baseline_map[conf.suite] = round(__valid_cnt / __cover_cnt * 100, 2)

        # result
        conf.type_src = "comb"
        cover_cnt, valid_cnt = codeql_accuracy(
            workspace, typecopilot_dir, os.path.join(groundtruth_dir, conf.suite), conf, False
        )
        codeql_typecopilot_map[conf.suite] = round(valid_cnt / cover_cnt * 100, 2)
        codeql_increase_map[conf.suite] = round(
            100 * (valid_cnt / cover_cnt - __valid_cnt / __cover_cnt), 2
        )

    return codeql_baseline_map, codeql_typecopilot_map, codeql_increase_map


if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")
    baseline_dir = os.path.join(workspace, "data-baseline")
    groundtruth_dir = os.path.join(workspace, "groundtruth")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    tbaa_baseline_map, tbaa_typecopilot_map, tbaa_increase_map = ae_tbaa(
        workspace, typecopilot_dir, baseline_dir
    )

    codeql_baseline_map, codeql_typecopilot_map, codeql_increase_map = ae_codeql(
        workspace, typecopilot_dir, baseline_dir, groundtruth_dir
    )

    coverage_baseline_map, coverage_typecopilot_map, coverage_increase_map = (
        ae_coverage(workspace, typecopilot_dir, baseline_dir)
    )

    table_data = []
    for suite in tbaa_baseline_map:
        table_data.append(
            [
                suite,
                str(tbaa_baseline_map[suite]) + "%",
                str(tbaa_typecopilot_map[suite])
                + "% ("
                + str(tbaa_increase_map[suite])
                + "pp↑)",
                str(codeql_baseline_map[suite]) + "%",
                str(codeql_typecopilot_map[suite])
                + "% ("
                + str(codeql_increase_map[suite])
                + "pp↑)",
                str(coverage_baseline_map[suite]) + "%",
                str(coverage_typecopilot_map[suite])
                + "% ("
                + str(coverage_increase_map[suite])
                + "pp↑)",
            ]
        )

    # average
    table_data.append(SEPARATING_LINE)
    table_data.append(
        [
            "Average",
            str(round(sum(tbaa_baseline_map.values()) / len(tbaa_baseline_map), 2))
            + "%",
            str(
                round(sum(tbaa_typecopilot_map.values()) / len(tbaa_typecopilot_map), 2)
            )
            + "% ("
            + str(round(sum(tbaa_increase_map.values()) / len(tbaa_increase_map), 2))
            + "pp↑)",
            str(round(sum(codeql_baseline_map.values()) / len(codeql_baseline_map), 2))
            + "%",
            str(
                round(
                    sum(codeql_typecopilot_map.values()) / len(codeql_typecopilot_map),
                    2,
                )
            )
            + "% ("
            + str(
                round(sum(codeql_increase_map.values()) / len(codeql_increase_map), 2)
            )
            + "pp↑)",
            str(
                round(
                    sum(coverage_baseline_map.values()) / len(coverage_baseline_map),
                    2,
                )
            )
            + "%",
            str(
                round(
                    sum(coverage_typecopilot_map.values())
                    / len(coverage_typecopilot_map),
                    2,
                )
            )
            + "% ("
            + str(
                round(
                    sum(coverage_increase_map.values()) / len(coverage_increase_map), 2
                )
            )
            + "pp↑)",
        ]
    )
    # output table
    print(
        tabulate(
            table_data,
            headers=[
                "Programs",
                "TBAA\nBaseline",
                "Ground Truth\nTypeCopilot",
                "CodeQL\nBaseline",
                "Ground Truth\nTypeCopilot",
                "Coverage\nBaseline",
                "\nTypeCopilot",
            ],
        )
    )
