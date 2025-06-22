import os
import subprocess
from conf import load_conf, Conf
import typecopilot
import typematcher


def profile_tbaa_accuracy(workspace, groundtruth_dir, conf: Conf):
    conf.log(True)
    prog_dir = os.path.join(workspace, "data-baseline", conf.suite)
    if not os.path.exists(prog_dir):
        os.makedirs(prog_dir)

    res_path = os.path.join(prog_dir, conf.program + ".tbaa.txt")

    if not os.path.exists(res_path):
        typecopilot.run(conf.bc_path, res_path, workspace, "tbaa", True)

    # parse result
    res_map = typematcher.load_res(res_path)
    global_var_count, global_valid_count = typematcher.eval_global(
        os.path.join(groundtruth_dir, conf.program + ".global.csv"), res_map
    )
    local_var_count, local_valid_count = typematcher.eval_local(
        os.path.join(groundtruth_dir, conf.program + ".local.csv"), res_map
    )

    total_cnt = typematcher.res_map_size(res_map)
    cover_cnt = global_var_count + local_var_count
    valid_cnt = global_valid_count + local_valid_count

    print(f"[RES] TBAA accuracy: {round(valid_cnt / cover_cnt * 100, 2)}%")


# return
def tbaa_profile(workspace, conf: Conf):
    cmd = f"opt -load-pass-plugin build/libTypeCopilot.so -passes=tbaaprofile {conf.bc_path}"
    process = subprocess.Popen(
        cmd,
        cwd=workspace,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    res = stderr.decode("utf-8").split("\n")

    tbaa_cnt = res[0].split(": ")[1]

    return int(tbaa_cnt)


if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    confs = load_conf("conf.yaml")
    for conf in confs:
        print(f"profiling {conf.program}'s TBAA metadata ...")
        tbaa_cnt = tbaa_profile(workspace, conf)


        # profile_tbaa_accuracy(
        #     workspace, os.path.join(workspace, "groundtruth", conf.suite), conf
        # )

        print(f"# TBAA: {tbaa_cnt}")