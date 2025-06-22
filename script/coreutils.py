import os
import subprocess
import argparse

# Bench applications
coreutils = [
    "basename",
    "basenc",
    "cat",
    "chcon",
    "chmod",
    "chown",
    "chroot",
    "cksum",
    "comm",
    "cp",
    "csplit",
    "cut",
    "date",
    "dd",
    "df",
    "dircolors",
    "dirname",
    "du",
    "echo",
    "env",
    "expand",
    "expr",
    "factor",
    "fmt",
    "fold",
    "getlimits",
    "groups",
    "head",
    "hostid",
    "id",
    "join",
    "kill",
    "link",
    "ln",
    "logname",
    "ls",
    "make-prime-list",
    "mkdir",
    "mkfifo",
    "mknod",
    "mktemp",
    "mv",
    "nice",
    "nl",
    "nohup",
    "nproc",
    "numfmt",
    "od",
    "paste",
    "pathchk",
    "pinky",
    "pr",
    "printenv",
    "printf",
    "ptx",
    "pwd",
    "readlink",
    "realpath",
    "rm",
    "rmdir",
    "runcon",
    "seq",
    "shred",
    "shuf",
    "sleep",
    "sort",
    "split",
    "stat",
    "stty",
    "sum",
    "sync",
    "tac",
    "tail",
    "tee",
    "test",
    "timeout",
    "touch",
    "tr",
    "truncate",
    "tsort",
    "tty",
    "uname",
    "unexpand",
    "uniq",
    "unlink",
    "uptime",
    "users",
    "who",
    "whoami",
]


# generate conf files for each coreutils binary
# usage: python3 coreutils.py >> conf.yaml
def gen_conf():
    template = """
- program: {0}
  suite: coreutils
  bc_path: bc/coreutils/src/{0}.bc
  codeql_path: bc/coreutils/codeql
  codeql_global_query: |
    import cpp
    from GlobalVariable gv
    where
        not gv.isInMacroExpansion() and
        not gv.getName().matches("(unnamed%") and
        not gv.getUnspecifiedType().getName().matches("(unnamed%") and
        not gv.getUnspecifiedType().getName().matches("struct <unnamed>%") and
        gv.getLocation().toString().matches("%src/{0}%")
    select gv, gv.getType(), gv.getUnspecifiedType()
  codeql_local_query: |
    import cpp
    from StackVariable lv
    where
        not lv.getFunction().isInline() and
        not lv.isInMacroExpansion() and
        not lv.getName().matches("(unnamed%") and 
        not lv.getUnspecifiedType().getName().matches("(unnamed%") and
        not lv.getUnspecifiedType().getName().matches("struct <unnamed>%") and
        lv.getLocation().toString().matches("%src/{0}%")
    select lv, lv.getFunction(), lv.getType(), lv.getUnspecifiedType()"""

    for prog in coreutils:
        print(template.format(prog), end="")


# extract bitcode
def extract_bc(coreutils_dir):
    for prog in coreutils:
        prog_bc_path = os.path.join(coreutils_dir, prog + ".bc")
        if os.path.exists(prog_bc_path):
            continue

        cmd = "extract-bc " + prog
        subprocess.check_output(cmd, cwd=coreutils_dir, shell=True)


def count_coverage(data_dir):
    for typesrc in ["mig", "di", "comb"]:
        total_count = 0
        cover_count = 0
        for prog in coreutils:
            coverage_path = os.path.join(
                data_dir, "coreutils", prog + "." + typesrc + ".coverage"
            )

            with open(coverage_path, "r") as f:
                lines = f.readlines()
                total_count += int(lines[0].split()[-1])
                cover_count += int(lines[1].split()[-1])

        print(
            "%s, %d, %d, %.2f"
            % (typesrc, total_count, cover_count, cover_count / total_count * 100)
        )


def count_codeql_accuracy(data_dir):
    for typesrc in ["mig", "di", "comb"]:
        cover_count = 0
        valid_count = 0
        for prog in coreutils:
            coverage_path = os.path.join(
                data_dir, "coreutils", prog + "." + typesrc + ".accuracy"
            )

            with open(coverage_path, "r") as f:
                lines = f.readlines()
                cover_count += int(lines[1].split()[-1])
                valid_count += int(lines[2].split()[-1])

    return cover_count, valid_count


def count_tbaa_accuracy(typecopilot_dir, baseline_dir):
    baseline_total_count = 0
    baseline_valid_count = 0
    typecopilot_total_count = 0
    typecopilot_valid_count = 0

    for prog in coreutils:
        base_tbaa_file = os.path.join(baseline_dir, prog + ".mig.tbaa")
        typecopilot_tbaa_file = os.path.join(typecopilot_dir, prog + ".comb.tbaa")

        with open(base_tbaa_file, "r") as f:
            lines = f.readlines()
            baseline_total_count += int(lines[0].split()[-1])
            baseline_valid_count += int(lines[1].split()[-1])

        with open(typecopilot_tbaa_file, "r") as f:
            lines = f.readlines()
            typecopilot_total_count += int(lines[0].split()[-1])
            typecopilot_valid_count += int(lines[1].split()[-1])

    # print(
    #     f"[RESULT] baseline accuracy: {round(baseline_valid_count / baseline_total_count * 100, 2)}%"
    # )
    # print(
    #     f"[RESULT] typecopilot accuracy: {round(typecopilot_valid_count / typecopilot_total_count * 100, 2)}%, increase: {round(100 * (typecopilot_valid_count / typecopilot_total_count - baseline_valid_count / baseline_total_count), 2)}%"
    # )

    return baseline_total_count, baseline_valid_count, typecopilot_total_count, typecopilot_valid_count


def dump_value(workspace, coreutils_dir):
    vaue_cnt = 0
    for prog in coreutils:
        bc_path = os.path.join(workspace, "bc/coreutils/src", prog + ".bc")
        cmd = f"make dump BC={bc_path}"
        process = subprocess.Popen(
            cmd,
            cwd=workspace,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = process.communicate()
        vaue_cnt += int(stderr.decode("utf-8").split("\n")[0].split(": ")[1])

    print(f"[RESULT] value count: {vaue_cnt}")


def count_tbaa(workspace, coreutils_dir):
    tbaa_total_cnt = 0
    for prog in coreutils:
        bc_path = os.path.join(workspace, "bc/coreutils/src", prog + ".bc")
        cmd = f"opt -load-pass-plugin build/libTypeCopilot.so -passes=tbaaprofile {bc_path}"
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
        tbaa_total_cnt += int(tbaa_cnt)

    print(f"[RESULT] tbaa count: {tbaa_total_cnt}")


def count_codeql(workspace):
    codeql_cnt = 0
    for prog in coreutils:
        codeql_file = os.path.join(
            workspace, "groundtruth/coreutils", prog + ".global.csv"
        )
        # count the number of lines in the file
        with open(codeql_file, "r") as f:
            codeql_cnt += len(f.readlines())

        codeql_file = os.path.join(
            workspace, "groundtruth/coreutils", prog + ".local.csv"
        )
        with open(codeql_file, "r") as f:
            codeql_cnt += len(f.readlines())

    print(f"[RESULT] codeql count: {codeql_cnt}")


if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    coreutils_dir = os.path.join(workspace, "bc/coreutils/src")

    parser = argparse.ArgumentParser()
    parser.add_argument("subcommand")
    args = parser.parse_args()

    if args.subcommand == "extract-bc":
        extract_bc(coreutils_dir)
    elif args.subcommand == "gen-conf":
        gen_conf()
    elif args.subcommand == "count-coverage":
        print("[LOG] baseline")
        baseline_dir = os.path.join(workspace, "data-baseline")
        count_coverage(baseline_dir)

        print("[LOG] typecopilot")
        typecopilot_dir = os.path.join(workspace, "data-typecopilot")
        count_coverage(typecopilot_dir)
    elif args.subcommand == "count-accuracy":
        print("[LOG] baseline")
        baseline_dir = os.path.join(workspace, "data-baseline")
        count_accuracy(baseline_dir)

        print("[LOG] typecopilot")
        typecopilot_dir = os.path.join(workspace, "data-typecopilot")
        count_accuracy(typecopilot_dir)
    elif args.subcommand == "count-tbaa-accuracy":
        baseline_dir = os.path.join(workspace, "data-baseline/coreutils")
        typecopilot_dir = os.path.join(workspace, "data-typecopilot/coreutils")
        count_tbaa_accuracy(typecopilot_dir, baseline_dir)
    elif args.subcommand == "dump-value":
        dump_value(workspace, coreutils_dir)
    elif args.subcommand == "count-tbaa":
        count_tbaa(workspace, coreutils_dir)
    elif args.subcommand == "count-codeql":
        count_codeql(workspace)
    else:
        parser.print_help()
