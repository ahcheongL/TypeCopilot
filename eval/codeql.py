import os
import re
import subprocess

DEFAULT_LOCAL_QUERY = """
import cpp

from StackVariable lv
where
  not lv.getFunction().isInline() and
  not lv.isInMacroExpansion() and
  not lv.getName().matches("(unnamed%") and 
  not lv.getUnspecifiedType().getName().matches("(unnamed%") and
  not lv.getUnspecifiedType().getName().matches("struct <unnamed>%")
select lv, lv.getFunction(), lv.getType(), lv.getUnspecifiedType()
"""

DEFAULT_GLOBAL_QUERY = """
import cpp

from GlobalVariable gv
where
  not gv.isInMacroExpansion() and
  not gv.getName().matches("(unnamed%") and
  not gv.getUnspecifiedType().getName().matches("(unnamed%") and
  not gv.getUnspecifiedType().getName().matches("struct <unnamed>%")
select gv, gv.getType(), gv.getUnspecifiedType()
"""


### Execute codeql queries
# query: query scripts
# db: path to codeql database
def run(workspace, query, db, bqrs_file, csv_file):
    if os.path.exists(csv_file):
        return

    with open(".ql", "w") as f:
        f.write(query)

    run_cmd = "codeql query run -d=%s -o=%s eval/.ql" % (db, bqrs_file)
    subprocess.run([run_cmd], shell=True, cwd=workspace)

    run_cmd = "codeql bqrs decode %s --format=csv -o=%s" % (bqrs_file, csv_file)
    subprocess.run([run_cmd], shell=True, cwd=workspace)

    lines = set()
    with open(csv_file, "r") as file:
        lines = set(file.readlines()[1:])
    with open(csv_file, "w") as file:
        file.write("".join(lines))

    os.remove(bqrs_file)
    os.remove(".ql")


type_map = {
    "bool": "i1",
    "char": "i8",
    "unchar": "i8",
    "short": "i16",
    "int": "i32",
    "unint": "i32",
    "long": "i64",
    "unlong": "i64",
    "longlong": "i64",
}


def transform_type(type, enumset):
    # remove signed, unsigned
    type = type.replace("unsigned ", "")
    type = type.replace("signed ", "")
    type = type.replace("const ", "")
    type = type.replace("volatile ", "")
    type = re.sub(r"^__attribute.*?\s", "", type)

    # remove whitespaces
    type = type.replace(" ", "")

    # transform array indexes
    num_brackets = type.count("[")
    type = re.sub(r"\[\d*\]", "", type)
    type += "*" * num_brackets

    # transform base types
    unptred_type = type.replace("*", "")
    if unptred_type in type_map:
        type = type.replace(unptred_type, type_map[unptred_type])
    if enumset and unptred_type in enumset:
        type = "i32"

    return type
