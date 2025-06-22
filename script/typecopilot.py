import os
import subprocess


### runner
# prog: program name
# bc_path: bitcode path
# workspace: current workspace path
# typesrc: type source
def run(bc_path, res_path, workspace, typesrc, baseline=False, worklist=True):
    # no bitcode, extract
    # if typesrc == "comb" or typesrc == "di":  # comb mode needs debug info
    #     bc_file = prog + "-di.bc"
    # else:
    #     bc_file = prog + ".bc"

    # no run result
    if not os.path.exists(res_path):
        run_cmd = f"make run BC={bc_path} TYPE_SRC={typesrc} BASELINE={baseline} DUMP_TYPE=true WL={worklist}"

        with open(res_path, "w") as f:
            subprocess.run(
                [run_cmd],
                cwd=workspace,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=f,
            )


# prog: program name
# bc_path: bitcode path
# workspace: current workspace path
# typesrc: type source
def coverage(bc_path, res_path, workspace, typesrc, baseline=False, worklist=True):
    # no run result
    if not os.path.exists(res_path):
        run_cmd = f"make run BC={bc_path} TYPE_SRC={typesrc} BASELINE={baseline} COVERAGE=true WL={worklist}"

        with open(res_path, "w") as f:
            subprocess.run(
                [run_cmd],
                cwd=workspace,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=f,
            )
