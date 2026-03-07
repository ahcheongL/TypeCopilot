#pragma once

#include <execinfo.h>
#include <llvm/ADT/StringExtras.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Type.h>
#include <llvm/IR/Value.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/FileSystem.h>

#include <iomanip>
#include <map>
#include <set>

#include "TypeSet.hpp"

extern cl::opt<string> TypeSrc;

using namespace std;
using namespace llvm;

class LLVMHelper;

extern cl::opt<string> OutputPath;

/// This class maintains a map from llvm values to the possible types.
class TypeGraph {
  using TypeMap = map<Value *, TypeSet *>;

 private:
  const bool DEBUG = false;

  bool canFlow(string type);

  bool canFlow(set<string> typeset);

  bool isInternal(Value *v);

 public:
  TypeMap                    globalMap;
  map<Function *, TypeMap *> localMap;

  ~TypeGraph();

  /// get the type of a value
  TypeSet *get(Function *scope, Value *key);

  /// merge multiple types into one value's type
  // return true if the type is updated, false if not changed
  bool put(Function *scope, Value *key, TypeSet *value, bool isFunc = false);

  /// merge a single type into one value's type
  bool put(Function *scope, Value *key, string value, bool isFunc = false);

  /// check if a value is an opaque pointer
  bool isOpaque(Function *scope, Value *key);

  /// get the pointer type of a value
  TypeSet *reference(Function *scope, Value *key);

  /// get the dereferenced type of a value
  TypeSet *dereference(Function *scope, Value *key);

  /// print the type of a value
  void dumpType(Function *scope, Value *key, TypeSet *value,
                std::set<std::string> &struct_types, llvm::raw_ostream *os);

  void dumpAllType(llvm::Module *module, LLVMHelper *llhelper);

  void              coverage(Module *module);
  vector<TypeMap *> getAllMap();

  int varSize();
};