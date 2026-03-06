import argparse
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
def coverage(bc_path, output_fn):

    TA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cmd = [
        "opt",
        "-load-pass-plugin",
        f"{TA_DIR}/build/libTypeCopilot.so",
        "-passes=typecopilot",
        "-output-path",
        output_fn,
        bc_path,
        "-o",
        "/dev/null",
    ]

    if os.path.exists(output_fn):
        if os.path.isdir(output_fn):
            print(
                f"Error: {output_fn} is a directory. Please provide a valid file path."
            )
            return

        os.remove(output_fn)
        return

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(output_fn) or process.returncode != 0:
        print(f"Error: Failed to generate {output_fn}.")
        print("Stdout:", process.stdout.decode())
        print("Stderr:", process.stderr.decode())
        return

    print(f"TypeCopilot result saved to {output_fn}")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TypeCopilot")
    parser.add_argument(
        "--bc_path", "-b", type=str, required=True, help="Path to the bitcode file"
    )
    parser.add_argument(
        "--output", "-o", type=str, required=True, help="Path to the result file"
    )

    args = parser.parse_args()

    run(
        args.bc_path,
        args.output,
    )
