from typing import List
from codeql import DEFAULT_LOCAL_QUERY, DEFAULT_GLOBAL_QUERY
import yaml


class Conf:
    def __init__(
        self,
        suite,
        program,
        bc_path,
        codeql_path,
        type_src,
        codeql_local_query,
        codeql_global_query,
        worklist,
    ) -> None:
        self.suite = suite
        self.program = program
        self.bc_path = bc_path
        self.codeql_path = codeql_path
        self.type_src = type_src
        self.codeql_local_query = codeql_local_query
        self.codeql_global_query = codeql_global_query
        self.worklist = worklist
    def log(self, baseline=False):
        print(
                f"[LOG] program: {self.program}, bc_path: {self.bc_path}, codeql_path: {self.codeql_path}, type_src: {self.type_src}, baseline: {baseline}, worklist: {self.worklist}"
        )


def dict_to_conf(d: dict):
    return Conf(
        suite=d.get("suite"),
        program=d.get("program"),
        bc_path=d.get("bc_path"),
        codeql_path=d.get("codeql_path"),
        type_src=d.get("type_src", ""),
        codeql_local_query=d.get("codeql_local_query", DEFAULT_LOCAL_QUERY),
        codeql_global_query=d.get("codeql_global_query", DEFAULT_GLOBAL_QUERY),
        worklist=d.get("worklist", True),
    )


def load_conf(conf_path) -> List[Conf]:
    # load list of conf from json
    with open(conf_path, "r") as f:
        confs = yaml.safe_load(f)
        return [dict_to_conf(conf) for conf in confs]
