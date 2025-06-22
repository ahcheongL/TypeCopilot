import os
import subprocess
import codeql
import csv
import re
from conf import Conf, load_conf


def run_valuedumper(workspace, bc_path, res_path):
    if not os.path.exists(res_path):

        with open(res_path, "w") as f:
            run_cmd = "make dump BC=" + bc_path
            print("[LOG] running valuedumper using:", run_cmd)
            subprocess.run(
                [run_cmd],
                cwd=workspace,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=f,
            )

    res_map = {}
    with open(res_path, "r") as f:
        for line in f.readlines():
            scope, var = line.split(", ", 1)
            var = var.strip()

            # trim the ending digis
            pattern = r"\.\d+$"
            var = re.sub(pattern, "", var)

            if res_map.get(scope) == None:
                res_map[scope] = [var]
            else:
                res_map[scope].append(var)

    return res_map


# generate groundtruth
def gen(workspace, groundtruth_dir, run_conf: Conf):
    # create groundtruth directory for specific program
    prog_dir = os.path.join(groundtruth_dir, run_conf.suite)
    if not os.path.exists(prog_dir):
        os.makedirs(prog_dir)

    # csv files
    raw_global_csv = os.path.join(prog_dir, run_conf.program + ".raw.global.csv")
    raw_local_csv = os.path.join(prog_dir, run_conf.program + ".raw.local.csv")

    global_csv = os.path.join(prog_dir, run_conf.program + ".global.csv")
    local_csv = os.path.join(prog_dir, run_conf.program + ".local.csv")

    # execute codeql to get raw results
    codeql.run(
        workspace,
        conf.codeql_global_query,
        conf.codeql_path,
        os.path.join(prog_dir, conf.program + ".raw.global.bqrs"),
        raw_global_csv,
    )

    codeql.run(
        workspace,
        conf.codeql_local_query,
        conf.codeql_path,
        os.path.join(prog_dir, conf.program + ".raw.local.bqrs"),
        raw_local_csv,
    )

    # execute valuedumper to get all variables dump
    res_map = run_valuedumper(
        workspace, run_conf.bc_path, os.path.join(prog_dir, run_conf.program + ".dump")
    )

    # intersect codeql and valuedumper results
    if not os.path.exists(global_csv):
        with open(raw_global_csv, "r") as f, open(global_csv, "w") as f_out:
            for row in csv.reader(f):
                name = row[0]
                scope = "(global)"

                if res_map.get(scope) == None or name not in res_map[scope]:
                    continue

                f_out.write(",".join(row) + "\n")

    if not os.path.exists(local_csv):
        with open(raw_local_csv, "r") as f, open(local_csv, "w") as f_out:
            for row in csv.reader(f):
                name = row[0]
                scope = row[1]

                if res_map.get(scope) == None or name not in res_map[scope]:
                    continue

                f_out.write(",".join(row) + "\n")


# This script is to generate the ground-truth by intersecting codeql and results from value dumper.
if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    groundtruth_dir = os.path.join(workspace, "groundtruth")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    if not os.path.exists(groundtruth_dir):
        os.makedirs(groundtruth_dir)

    # kernel
    confs = load_conf("conf.yaml")
    for conf in confs:
        conf.log()
        gen(workspace, groundtruth_dir, conf)
