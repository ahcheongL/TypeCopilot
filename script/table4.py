import os
import subprocess
from tabulate import tabulate


def mlta(branch, mlta_dir, target):
    cmd = (
        f"git checkout {branch} && make clean && make && ./build/lib/kanalyzer {target}"
    )
    process = subprocess.Popen(
        cmd, cwd=mlta_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # check error
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(stderr.decode("utf-8"))
        raise Exception("MLTA failed to run")

    res = stderr.decode("utf-8").strip().split("\n")

    # get the last line and parse the final int
    callsite = int(res[-2].split(":")[-1].strip())
    callee = int(res[-1].split(":")[-1].strip())

    return callsite, callee


if __name__ == "__main__":
    mlta_dir = os.path.join("/root", "mlta")
    bc_dir = os.path.join("/root", "typecopilot", "bc")
    table = []

    # baseline
    _, baseline_avg = mlta("baseline", mlta_dir, os.path.join(bc_dir, "linux.bc"))

    # modified
    modified_callsite, modified_callee = mlta(
        "op", mlta_dir, os.path.join(bc_dir, "linux.bc")
    )

    # integration
    integration_callsite, integration_callee = mlta(
        "integration", mlta_dir, os.path.join(bc_dir, "linux.bc")
    )

    # original
    original_callsite, original_callee = mlta(
        "main", mlta_dir, os.path.join(bc_dir, "llvm14-linux.bc")
    )

    # integration 14
    integration_14_callsite, integration_14_callee = mlta(
        "integration-14", mlta_dir, os.path.join(bc_dir, "llvm14-linux.bc")
    )

    table.append(
        [
            "MLTA Integration",
            "Baseline",
            "Modified",
            "TypeCopilot",
            "Original 14",
            "TypeCopilot",
        ]
    )
    table.append(["#iCall", "", _, "", original_callsite, ""])
    table.append(
        [
            "Avg. Target",
            baseline_avg,
            int(modified_callee / modified_callsite),
            round(integration_callee / integration_callsite, 1),
            round(original_callee / original_callsite, 1),
            round(integration_14_callee / integration_14_callsite, 1),
        ]
    )

    print(tabulate(table, headers=["LLVM Version", "", "LLVM-16", "", "LLVM-14", ""]))
