#include "TypeGraph.hpp"

#include <iostream>
#include <queue>

#include "LLVMHelper.hpp"

extern cl::opt<string> TypeSrc;

using namespace std;
using namespace llvm;

extern cl::opt<string> OutputPath;

class LLVMHelper;

inline void print_stacktrace(void) {
  errs() << "stack trace:\n";
  char **strings;
  size_t i, size;
  enum Constexpr { MAX_SIZE = 1024 };
  void *array[MAX_SIZE];
  size = backtrace(array, MAX_SIZE);
  strings = backtrace_symbols(array, size);
  for (i = 0; i < size; i++)
    errs() << strings[i] << "\n";
  free(strings);
}

bool TypeGraph::canFlow(string type) {
  return !type.empty() && type != "ptr";
}

bool TypeGraph::canFlow(set<string> typeset) {
  return !typeset.empty() && !typeset.count("ptr");
}

bool TypeGraph::isInternal(Value *v) {
  auto name = v->getName();
  if (name.starts_with(".")) return true;
  if (name.count(".") > 1) return true;
  if (name.count(".") == 1) {
    auto subname = name.split(".").second;
    for (auto ch : subname) {
      if (!isDigit(ch)) return true;
    }
  }

  return false;
}

TypeGraph::~TypeGraph() {
  for (auto &pair : globalMap) {
    delete pair.second;
  }
  for (auto &pair : localMap) {
    for (auto &pair2 : *pair.second) {
      delete pair2.second;
    }
    delete pair.second;
  }
}

/// get the type of a value
TypeSet *TypeGraph::get(Function *scope, Value *key) {
  // first check local type
  if (scope && localMap.find(scope) != localMap.end()) {
    TypeMap *localTypeMap = localMap[scope];
    auto     it = localTypeMap->find(key);
    if (it != localTypeMap->end()) return it->second;
  }

  // check global type
  auto it = globalMap.find(key);
  if (it != globalMap.end()) return it->second;

  return nullptr;
}

/// merge multiple types into one value's type
// return true if the type is updated, false if not changed
bool TypeGraph::put(Function *scope, Value *key, TypeSet *value, bool isFunc) {
  // no value, quick return
  if (!value) return false;

  TypeSet *to_add = new TypeSet();
  to_add->insert(value);

  // find existing type
  auto old = get(scope, key);

  if (old) {
    // filter out ptr* type
    // FIXME delete stale debug stuff
    if (DEBUG && to_add->count("ptr**")) {
      key->dump();
      errs() << "current type: ";
      old->dump();
      errs() << "\n";
      print_stacktrace();
    }

    // filter out subtype problems
    for (auto &type : to_add->getTypes()) {
      // if old contains type.reference(), then skip
      if (old->count(type + "*")) {
        to_add->erase(type);
      } else if (type.back() == '*' &&
                 old->count(type.substr(0, type.size() - 1))) {
        // if old contains type.dereference(), then skip
        to_add->erase(type);
      }
    }
  }

  if (old == nullptr) old = new TypeSet();

  if (to_add->empty()) {
    delete to_add;
    return false;
  }

  // check if old == value
  if (old->equals(to_add)) {
    delete to_add;
    return false;
  }

  // update type
  old->insert(to_add);
  delete to_add;

  if (isFunc) old->isFunc = true;

  if (scope) {  // test scope
    auto it = localMap.find(scope);
    if (it != localMap.end())  // update local map
      (*it->second)[key] = old;
    else {
      localMap[scope] = new TypeMap();
      (*localMap[scope])[key] = old;
    }
  } else {  // no scope, update global map
    globalMap[key] = old;
  }

  return true;
}

/// merge a single type into one value's type
bool TypeGraph::put(Function *scope, Value *key, string value, bool isFunc) {
  // find existing type
  auto old = get(scope, key);

  if (old) {
    // filter out ptr* type
    if (DEBUG && value == "ptr**") {
      key->dump();
      errs() << "current type: ";
      old->dump();
      errs() << "\n";
      print_stacktrace();
    }

    // filter out subtype problems
    if (old->count(value + "*")) {
      return false;
    } else if (value.back() == '*' &&
               old->count(value.substr(0, value.size() - 1))) {
      return false;
    }
  }

  if (old == nullptr) old = new TypeSet();

  // check if old == value
  if (old->count(value)) return false;

  // update type
  old->insert(value);

  if (isFunc) old->isFunc = true;

  // should not be a global value
  if (!dyn_cast<GlobalValue>(key) && scope) {
    auto it = localMap.find(scope);
    if (it != localMap.end())  // update local map
      (*it->second)[key] = old;
    else {
      localMap[scope] = new TypeMap();
      (*localMap[scope])[key] = old;
    }
  } else {  // no scope, update global map
    globalMap[key] = old;
  }

  return true;
}

/// check if a value is an opaque pointer
bool TypeGraph::isOpaque(Function *scope, Value *key) {
  auto typeSet = get(scope, key);
  return typeSet && typeSet->count("ptr");
}

/// get the pointer type of a value
TypeSet *TypeGraph::reference(Function *scope, Value *key) {
  auto ret = new TypeSet();
  auto old = get(scope, key);

  if (!old) return ret;

  for (auto &type : old->getTypes()) {
    // if type ends with "**", skip ***p
    if (type.size() > 2 && type.substr(type.size() - 2) == "**") { continue; }

    if (type != "ptr") ret->insert(type + "*");
  }

  return ret;
}

/// get the dereferenced type of a value
TypeSet *TypeGraph::dereference(Function *scope, Value *key) {
  auto ret = new TypeSet();
  auto old = get(scope, key);

  if (!old) return ret;

  for (auto &type : old->getTypes()) {
    if (type.back() == '*') { ret->insert(type.substr(0, type.size() - 1)); }
  }

  return ret;
}

/// print the type of a value
void TypeGraph::dumpType(Function *scope, Value *key, TypeSet *value,
                         std::set<std::string> &struct_types,
                         llvm::raw_ostream     *os) {
  if (!key->hasName()) { return; }

  value->erasePtr();
  if (value->empty()) { return; }

  if (scope)
    (*os) << scope->getName() << ", ";
  else
    (*os) << "(global), ";

  (*os) << key->getName() << ", { ";

  if (!value->empty()) {
    set<string>::iterator iter = value->begin();
    (*os) << *iter;
    while (++iter != value->end())
      (*os) << ", " << *iter;
  }
  (*os) << " }\n";

  set<string>::iterator iter = value->begin();
  while (iter != value->end()) {
    string type = *iter;
    while (type.back() == '*') {
      type.pop_back();
    }

    if (type.find("%struct.") == 0) { struct_types.insert(type.substr(1)); }
    if (type.find("%union.") == 0) { struct_types.insert(type.substr(1)); }
    if (type.find("%class.") == 0) { struct_types.insert(type.substr(1)); }
    iter++;
  }
  return;
}

void TypeGraph::dumpAllType(llvm::Module *module, LLVMHelper *llhelper) {
  llvm::raw_ostream                    *os = &errs();
  std::unique_ptr<llvm::raw_fd_ostream> file_os;

  if (OutputPath != "") {
    std::error_code EC;
    file_os = std::make_unique<llvm::raw_fd_ostream>(OutputPath, EC,
                                                     llvm::sys::fs::OF_Append);
    if (EC) {
      errs() << "Could not open file: " << EC.message() << "\n";
    } else {
      os = file_os.get();
    }
  }

  std::set<std::string> struct_type_names;
  for (auto &pair : globalMap) {
    dumpType(nullptr, pair.first, pair.second, struct_type_names, os);
  }
  for (auto &pair : localMap) {
    for (auto &pair2 : *pair.second) {
      dumpType(pair.first, pair2.first, pair2.second, struct_type_names, os);
    }
  }

  errs() << "dumped all types, now dumping struct types...\n";
  errs() << "Found " << struct_type_names.size() << " struct types\n";

  if (TypeSrc.getValue() != "comb") {
    if (file_os) { file_os->close(); }
    return;
  }

  auto combHelper = (CombHelper *)(llhelper);
  (*os) << "\nstruct types:\n";

  std::vector<llvm::StructType *> all_struct_types =
      module->getIdentifiedStructTypes();

  std::queue<std::string> struct_type_queue;
  for (const string &str : struct_type_names) {
    struct_type_queue.push(str);
  }

  std::set<std::string> dumped_struct_types;

  while (!struct_type_queue.empty()) {
    std::string struct_type_name = struct_type_queue.front();
    struct_type_queue.pop();

    if (dumped_struct_types.count(struct_type_name) != 0) { continue; }

    llvm::StructType *struct_type = nullptr;
    for (auto st : all_struct_types) {
      if (st->getName() == struct_type_name) {
        struct_type = st;
        break;
      }
    }

    if (!struct_type) {
      errs() << "Could not find struct type: " << struct_type_name << "\n";
      continue;
    }

    dumped_struct_types.insert(struct_type_name);

    (*os) << struct_type_name << ":";
    for (uint32_t idx = 0; idx < struct_type->getNumElements(); idx++) {
      string field_type_name = combHelper->getDIStructField(struct_type, idx);
      (*os) << field_type_name << ",";

      while (field_type_name.back() == '*') {
        field_type_name.pop_back();
      }

      if (field_type_name.find("struct.") == 0 ||
          field_type_name.find("union.") == 0 ||
          field_type_name.find("class.") == 0) {
        if (dumped_struct_types.count(field_type_name) == 0) {
          struct_type_queue.push(field_type_name);
        }
      }
    }
    (*os) << "\n";
  }

  if (file_os) { file_os->close(); }
  return;
}

void TypeGraph::coverage(Module *module) {
  int total_cnt = 0;
  int cover_cnt = 0;

  // globals
  for (auto &global : module->globals()) {
    // skip if global is a function
    // if (global.getType()->isFunctionTy())
    //     continue;
    total_cnt++;

    Value *v = dyn_cast<Value>(&global);
    auto   type = get(nullptr, v);
    if (type && !type->isOpaque())
      cover_cnt++;
    else {
      // FIXME missing
      // errs() << "[DBG] missing global: " << global << "\n";
    }
  }

  // arguments
  for (auto &F : *module) {
    Function *scope = dyn_cast<Function>(&F);

    for (auto &arg : F.args()) {
      total_cnt++;
      auto type = get(scope, &arg);
      if (type && !type->isOpaque()) {
        cover_cnt++;
      } else {
        // FIXME missing
        // errs() << "[DBG] missing argument: " << arg << "\n";
      }
    }
    for (auto &BB : F) {
      for (auto &inst : BB) {
        if (auto store = dyn_cast<StoreInst>(&inst)) continue;

        total_cnt++;
        auto type = get(scope, dyn_cast<Value>(&inst));
        if (type && !type->isOpaque()) {
          cover_cnt++;
        } else {
          // FIXME missing
          // errs() << "[DBG] missing inst: " << inst << "\n";
        }
      }
    }
  }

  errs() << "[RESULT] total count: " << total_cnt << "\n";
  errs() << "[RESULT] cover count: " << cover_cnt << "\n";
  double coverage = (double)cover_cnt / total_cnt;

  ostringstream oss;
  oss << fixed << std::setprecision(2) << (coverage * 100) << "%";
  errs() << "[RESULT] coverage: " << oss.str() << "\n";
}

vector<TypeGraph::TypeMap *> TypeGraph::getAllMap() {
  vector<TypeGraph::TypeMap *> ret;
  ret.push_back(&globalMap);
  for (auto &pair : localMap) {
    ret.push_back(pair.second);
  }
  return ret;
}

int TypeGraph::varSize() {
  int ret = globalMap.size();
  for (auto &pair : localMap) {
    ret += pair.second->size();
  }
  return ret;
}