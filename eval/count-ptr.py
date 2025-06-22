import os
from conf import Conf, load_conf
from typematcher import load_res, get_res_type_set


# for each pointer type variable, count the size of typeset
def count_ptr(baseline_dir, typecopilot_dir, conf: Conf):
    # read baseline mig res
    baseline_res_path = os.path.join(
        baseline_dir, conf.suite, conf.program + ".di.txt"
    )
    baseline_res_map = load_res(baseline_res_path)

    # read typecopilot comb res
    typecopilot_res_path = os.path.join(
        typecopilot_dir, conf.suite, conf.program + ".comb.txt"
    )
    typecopilot_res_map = load_res(typecopilot_res_path)

    ptr_count = 0
    type_total_count = 0

    # for each { ptr }, check the result
    for scope, var_type_pair in baseline_res_map.items():
        for var, typeset in var_type_pair:
            if typeset == "{ void* }" and var != "":
                ptr_count += 1

                # this is the pointer type variable
                typecopilot_typeset = get_res_type_set(scope, var, typecopilot_res_map)

                # get count of { xxx, xxx }
                types = typecopilot_typeset[2:-2]
                types = types.split(", ")
                type_total_count += len(types)

                if len(types) > 1:
                    print(f"[DBG] {scope} {var} {typecopilot_typeset}")

    print("ptr count:", ptr_count)
    print("type total count:", type_total_count)
    print("average typeset size: {:.2f}".format(type_total_count / ptr_count))


if __name__ == "__main__":
    # read config
    baseline_dir = os.path.join(os.path.pardir, "data-baseline")
    typecopilot_dir = os.path.join(os.path.pardir, "data-typecopilot")

    confs = load_conf("conf.yaml")
    for conf in confs:
        count_ptr(baseline_dir, typecopilot_dir, conf)
