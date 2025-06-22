import os
from typing import List
from conf import load_conf, Conf
from typematcher import load_res, transform_llvm_type


class Count:
    # number of typeset
    single_type_cnt = 0
    multi_type_cnt = 0
    total_cnt = 0

    # reasoning about multi-type
    generic_ptr_cnt = 0
    field_struct_misuse_cnt = 0
    di_llvm_format_cnt = 0
    integer_bitwidth_mismatch_cnt = 0
    anonymous_struct_cnt = 0
    is_union_cnt = 0


def profile(workspace, res_dir, conf: Conf, count: Count):
    res_path = os.path.join(res_dir, conf.suite, conf.program + ".comb.txt")
    res_map = load_res(res_path)

    ll_file = conf.bc_path.replace(".bc", ".ll")
    ll_path = os.path.join(workspace, ll_file)

    with open(ll_path, "r") as f:
        ll_content = f.read()

    for scope, var_pair in res_map.items():
        for var, typeset in var_pair:
            types = typeset[2:-2].split(", ")
            count.total_cnt += 1

            if len(types) == 1:
                count.single_type_cnt += 1
            else:
                count.multi_type_cnt += 1

                # remove and profile anonymous structs
                types = [type for type in types if not is_anonymous_struct(type)]
                if len(types) == 1:
                    count.anonymous_struct_cnt += 1
                    continue

                # reasoning about multi-type
                if is_generic_ptr(types):
                    count.generic_ptr_cnt += 1
                elif is_integer_bitwidth_mismatch(types):
                    count.integer_bitwidth_mismatch_cnt += 1
                elif is_union(types):
                    count.is_union_cnt += 1
                elif is_di_llvm_format(types, ll_content):
                    count.di_llvm_format_cnt += 1
                elif is_field_struct_misuse(types, ll_content):
                    count.field_struct_misuse_cnt += 1
                else:
                    print(f"[DBG] Unknown multi-type: {types}")


def is_union(types: List[str]) -> bool:
    stripped_types = [type.strip("*") for type in types]
    for type in stripped_types:
        if type.startswith("union") or type.startswith("%union."):
            return True

    return False

# also remove the empty types
def is_anonymous_struct(type: str) -> bool:
    if type.strip("*") == "" or type.strip("*") == "%struct.":
        return True
    return False


def is_generic_ptr(types: List[str]) -> bool:
    return any(type == "void*" or type == "void**" for type in types)



def is_integer_bitwidth_mismatch(types: List[str]) -> bool:
    stripped_types = [type.strip("*") for type in types]

    # all types are integer (i32, i64, etc.)
    for type in stripped_types:
        if not type.startswith("i"):
            return False

        bitwidth = type[1:]
        # is number
        if not bitwidth.isdigit():
            return False

    return True

def check_field(field: str, struct_name: str, ll_list: List[str]) -> bool:
    found = False
    typedef = ""
    for ll in ll_list:
        if ll.startswith(struct_name + " = type "):
            typedef = ll
            found = True
            break
    if found:
        # check if the other type is the first field of the struct
        # get list of fields e.g.: { aaa, bbb }
        first_field = typedef.split("{")[1].split("}")[0].split(",")[0].strip()

        if field.strip("*") == first_field:
            return True
        if field == "i8*" and first_field == "ptr":
            return True

    return False



def is_field_struct_misuse(types: List[str], ll_content: List[str]) -> bool:
    if types[0] == types[1] + "*" or types[1] == types[0] + "*":
        return True

    stripped_types = [type.strip("*") for type in types]

    ll_list = ll_content.split("\n")

    if check_field(types[0], stripped_types[1], ll_list):
        return True
    if check_field(types[1], stripped_types[0], ll_list):
        return True

    return False



def is_di_llvm_format(types: List[str], ll_content) -> bool:
    # check all the elements have the same pointer level
    stripped_types = [type.strip("*") for type in types]

    if all(not type.startswith("%struct.") for type in stripped_types):
        return False

    for type in stripped_types:
        if type.startswith("%struct.") and type not in ll_content:
            return True

    return False


if __name__ == "__main__":
    workspace = os.path.abspath(os.path.pardir)
    typecopilot_dir = os.path.join(workspace, "data-typecopilot")

    confs = load_conf("conf.yaml")
    count = Count()
    for conf in confs:
        profile(workspace, typecopilot_dir, conf, count)

    print(f"Total type cnt: {count.total_cnt}")
    print(
        f"Single type ratio: {round(100 * count.single_type_cnt / count.total_cnt, 2)}%"
    )
    print(
        f"Multi type ratio: {round(100 * count.multi_type_cnt / count.total_cnt, 2)}%"
    )

    print("---")
    print(f"Multi type cnt: {count.multi_type_cnt}")
    print(f"Generic ptr cnt: {count.generic_ptr_cnt}")
    print(f"DI LLVM format cnt: {count.di_llvm_format_cnt}")
    print(f"Integer bitwidth mismatch cnt: {count.integer_bitwidth_mismatch_cnt}")
    print(f"Anonymous struct cnt: {count.anonymous_struct_cnt}")
    print(f"Union cnt: {count.is_union_cnt}")
    print(f"Field struct misuse cnt: {count.field_struct_misuse_cnt}")
    print(
        f"Leftover cnt: {count.multi_type_cnt - count.generic_ptr_cnt - count.di_llvm_format_cnt - count.integer_bitwidth_mismatch_cnt - count.anonymous_struct_cnt - count.is_union_cnt - count.field_struct_misuse_cnt}"
    )
