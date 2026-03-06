#pragma once

#include <llvm/IR/GlobalValue.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/PassManager.h>
#include <llvm/IR/ValueSymbolTable.h>
#include <llvm/Pass.h>
#include <llvm/PassRegistry.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/raw_ostream.h>

#include "LLVMHelper.hpp"

using namespace llvm;
using namespace std;

// This pass is used to check the count of total variables and named variables.
class ValueDumper : public PassInfoMixin<ValueDumper> {
 private:
  int total_cnt = 0;
  int named_cnt = 0;

  bool isInternal(Value *v) {
    if (!v->hasName()) return true;

    auto name = v->getName();
    if (name.starts_with(".")) return true;

    // if (name.count(".") > 1)
    //     return true;

    // if (name.starts_with("."))
    //     return true;

    // if (name.count(".") == 1) {
    //     auto subname = name.split(".").second;
    //     for (auto ch : subname) {
    //         if (!isDigit(ch))
    //             return true;
    //     }
    // }

    return false;
  }

  void countValues(Module &M) {
    for (auto &global : M.globals()) {
      // not a function
      if (isa<Function>(&global)) continue;

      total_cnt++;
      if (!isInternal(&global)) named_cnt++;
    }

    for (auto &F : M) {
      // param
      for (auto &param : F.args()) {
        total_cnt++;
        if (!isInternal(&param)) named_cnt++;
      }

      // inst
      for (auto &BB : F) {
        for (auto &inst : BB) {
          Value *v = dyn_cast<Value>(&inst);

          total_cnt++;
          if (!isInternal(v)) named_cnt++;
        }
      }
    }
  }

 public:
  PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
    countValues(M);

    errs() << "Total variables: " << total_cnt << "\n";
    errs() << "Named variables: " << named_cnt << "\n";
    // errs() << "Valid variables: " << valid_cnt << "\n";
    // errs() << "Opaque Pointers count: " << base_cnt << "\n";
    return PreservedAnalyses::all();
  }

  static bool isRequired() {
    return true;
  }
};
