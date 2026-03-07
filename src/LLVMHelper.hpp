#pragma once

#include <llvm/ADT/SmallVector.h>
#include <llvm/BinaryFormat/Dwarf.h>
#include <llvm/IR/DebugInfo.h>
#include <llvm/IR/DebugInfoMetadata.h>
#include <llvm/IR/DerivedTypes.h>
#include <llvm/IR/GlobalVariable.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Type.h>
#include <llvm/IR/Value.h>
#include <llvm/Support/Casting.h>

#include <map>
#include <string>

#include "TypeGraph.hpp"
#include "TypeHelper.hpp"

using namespace llvm;
using namespace std;

class LLVMHelper {
 public:
  TypeHelper   tyHelper;
  virtual void initialize(Module *module, TypeGraph *tg) = 0;
};

/// Helper class for LLVM migration instructions
class MigrationHelper : public LLVMHelper {
 public:
  void   initialize(Module *module, TypeGraph *tg);
  string getType(Instruction &inst);
};

class DebugInfoHelper : public LLVMHelper {
 private:
  const bool RESOLVE_TYPEDEF = true;

  map<StructType *, DIType *>             structMap;
  map<Value *, vector<DILocalVariable *>> diLocalMap;

 public:
  void initialize(Module *module, TypeGraph *tg);

  void parseDILocalVar(Instruction                             &inst,
                       map<Value *, vector<DILocalVariable *>> &diLocalMap);

  bool hasDebugInfo(Module &M);

  string getDIStructField(StructType *structType, uint64_t index);

  string getDITypeName(DIType *ditype);
};

class TBAAHelper : public LLVMHelper {
 public:
  void initialize(Module *module, TypeGraph *tg);

  bool isScalarType(string &type);

  string getTBAAType(MDNode *tbaa, Function &func, Instruction &inst);

  string getTypeName(MDNode *tbaaType);

  // parse TBAA type name
  string parseTypeName(MDNode *tbaa);
  bool   isOmnipotentChar(MDNode *tbaa);
};

class CombHelper : public LLVMHelper {
 private:
  MigrationHelper                        *migHelper;
  DebugInfoHelper                        *diHelper;
  map<StructType *, DIType *>             structMap;
  map<Value *, vector<DILocalVariable *>> diLocalMap;

 public:
  void initialize(Module *module, TypeGraph *tg);

  bool hasDebugInfo(Module &M);

  string getDIStructField(StructType *structType, uint64_t index);
};