import os
import subprocess
from conf import Conf, load_conf


def tbaa_accuracy(workspace, res_dir, conf: Conf, baseline=False):
    conf.log(baseline)

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
        cmd = f"opt -load-pass-plugin build/libTypeCopilot.so -passes=typecopilot -tbaa-acc=true -baseline={baseline} -type-src={conf.type_src} {conf.bc_path}"
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


if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")
    baseline_dir = os.path.join(workspace, "data-baseline")
    subprocess.check_output(["make"], cwd=workspace, shell=True)

    confs = load_conf("conf.yaml")
    for conf in confs:
        # baseline
        conf.type_src = "mig"
        __total_cnt, __valid_cnt = tbaa_accuracy(workspace, baseline_dir, conf, True)
        print(f"[RESULT] baseline accuracy: {round(__valid_cnt / __total_cnt * 100, 2)}%")

        # result
        conf.type_src = "comb"
        total_cnt, valid_cnt = tbaa_accuracy(workspace, typecopilot_dir, conf, False)
        if total_cnt != 0:
            increase = round(100 * (valid_cnt / total_cnt - __valid_cnt / __total_cnt), 2)
            print(
                f"[RESULT] typecopilot accuracy: {round(valid_cnt / total_cnt * 100, 2)}%, increase: {increase}%"
            )
