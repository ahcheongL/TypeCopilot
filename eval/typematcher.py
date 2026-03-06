import codeql
import csv
import re
import os


DEBUG = False


def transform_llvm_type(type):
    unptred_type = type.replace("*", "")
    # if unptred_type == "i1":
    # type = type.replace("i1", "i8")
    if unptred_type == "_Bool":
        type = type.replace("_Bool", "i1")
    if unptred_type == "char":
        type = type.replace("char", "i8")
    if unptred_type == "short":
        type = type.replace("short", "i16")
    if unptred_type == "int":
        type = type.replace("int", "i32")
    if unptred_type == "long":
        type = type.replace("long", "i64")
    if unptred_type == "unsigned int":
        type = type.replace("unsigned int", "i32")
    if unptred_type == "unsigned long":
        type = type.replace("unsigned long", "i64")
    if unptred_type == "long long":
        type = type.replace("long long", "i64")
    if unptred_type == "u_char":
        type = type.replace("u_char", "i8")
    if unptred_type == "unsigned char":
        type = type.replace("unsigned char", "i8")
    if unptred_type == "ptr":
        type = type.replace("ptr", "void*")

    if type.starts_with("%struct."):
        type = type.replace("%struct.", "")
    if type.starts_with("%union."):
        type = type.replace("%union.", "")

    if type.starts_with("enum "):
        type = type.replace("enum ", "")
    if type.starts_with("struct "):
        type = type.replace("struct ", "")
    if type.starts_with("union "):
        type = type.replace("union ", "")

    if unptred_type.starts_with("<") and unptred_type.endswith(">"):
        type = type.split(" ")[2]
        type = type.replace(">", "") + "*"

    return type


def check_type_match(run_type_set: str, type, enumset=None):
    codeql_type = codeql.transform_type(type, enumset)
    run_type = run_type_set[2:-2]
    run_type = run_type.split(", ")

    for ty in run_type:
        llvm_type = transform_llvm_type(ty)

        if llvm_type == codeql_type:  # check the original type matches
            return True
        if llvm_type == codeql_type + "*":  # check the ptred type matches
            return True

    return False


def eval_global(bench_path, res_map):
    # count
    global_count = 0
    global_valid_count = 0

    # do evaluation
    with open(bench_path, "r") as file:
        for row in csv.reader(file, delimiter=","):
            name = row[0]
            type = row[1]
            unspecified_type = row[2]

            run_type_set = get_res_type_set("(global)", name, res_map)
            if not run_type_set:
                continue

            global_count += 1
            if check_type_match(run_type_set, type) or check_type_match(
                run_type_set, unspecified_type
            ):
                global_valid_count += 1
            elif DEBUG:
                print(
                    "[DBG] mismatch in global var %s, our: %s, bench: %s (%s)"
                    % (name, run_type_set, type, unspecified_type)
                )

    return global_count, global_valid_count


def eval_local(bench_path, res_map):
    # count
    local_count = 0
    local_valid_count = 0

    # do evaluation
    with open(bench_path, "r") as file:
        for row in csv.reader(file, delimiter=","):
            name = row[0]
            scope = row[1]
            type = row[2]
            unspecified_type = row[3]

            run_type_set = get_res_type_set(scope, name, res_map)
            if run_type_set == None:
                continue

            local_count += 1
            if check_type_match(run_type_set, type) or check_type_match(
                run_type_set, unspecified_type
            ):
                local_valid_count += 1
            elif DEBUG:
                # if not run_type_set == "{ ptr }":
                print(
                    "[DBG] mismatch in scope: %s, var name: %s, our: %s, bench: %s (%s)"
                    % (scope, name, run_type_set, type, unspecified_type)
                )

    return local_count, local_valid_count


def get_res_type_set(scope, name, res_map):
    if res_map.get(scope) == None:
        return None
    else:
        for var, typeset in res_map[scope]:
            if var == name:
                return typeset

    return None


# load the result of type inference
def load_res(run_path):
    res_map = {}

    with open(run_path, "r") as f:
        for line in f.readlines():
            run_scope, var, typeset = line.split(", ", 2)

            # trim the ending digis
            pattern = r"\.\d+$"
            var = re.sub(pattern, "", var)

            if res_map.get(run_scope) == None:
                res_map[run_scope] = [(var, typeset.strip())]
            else:
                res_map[run_scope].append((var, typeset.strip()))

    return res_map


def res_map_size(res_map):
    size = 0
    for scope in res_map:
        for var, typeset in res_map[scope]:
            if not typeset == "{ ptr }":
                size += 1
    return size


def res_map_size_with_op(res_map):
    size = 0
    for scope in res_map:
        size += len(res_map[scope])
    return size
