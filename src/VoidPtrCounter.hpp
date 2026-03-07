#pragma once

#include <llvm/IR/Function.h>
#include <llvm/IR/Instruction.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/PassManager.h>
#include <llvm/Support/raw_ostream.h>

#include "TypeAnalyzer.hpp"
#include "TypeGraph.hpp"

using namespace llvm;
using namespace std;

extern cl::opt<string> TypeSrc;

/// This pass counts the number of void pointers in the module and trace how
/// they are used or assigned.
class VoidPtrCounter : public PassInfoMixin<VoidPtrCounter> {
 private:
  void dumpFunctionHeader(llvm::Function &function) {
    // Print the function's return type
    llvm::errs() << "[*] define " << *function.getReturnType() << " @"
                 << function.getName() << "(";

    // Print the parameters
    bool first = true;
    for (auto &arg : function.args()) {
      if (!first) { llvm::errs() << ", "; }
      first = false;
      llvm::errs() << *arg.getType() << " %" << arg.getName();
    }
    llvm::errs() << ")\n";  // Close the function declaration
  }

  bool passedAsArg(Function *func, CallInst *callsite) {
    // 1. call to another function
    auto calledFunc = callsite->getCalledFunction();
    if (calledFunc == func) return false;

    // 2. passed as an argument
    for (auto &arg : callsite->args()) {
      auto argAsFunc = dyn_cast<Function>(arg.get());
      if (argAsFunc && argAsFunc == func) return true;
    }

    return false;
  }

  /*
   * Lookup Def-Use chain for each void pointer.
   * Return if the value should be filtered out.
   */
  bool lookupDUChain(Value *value) {
    set<Value *>   visited;
    queue<Value *> worklist;
    worklist.push(value);

    bool filter = false;

    while (!worklist.empty()) {
      // get next
      auto to_visit = worklist.front();
      worklist.pop();

      // visited
      if (visited.count(to_visit)) continue;
      visited.insert(to_visit);

      // dump and analyze
      if (Argument *arg = dyn_cast<Argument>(to_visit)) {
        auto func = arg->getParent();
        dumpFunctionHeader(*func);

        // not called, useless function
        if (func->user_empty()) { return true; }

        // get all callsite
        for (auto user : func->users()) {
          errs() << "[*] (call) " << *user << "\n";
          worklist.push(user);

          // TODO handle indirect call
          // function is passed into another function as parameter
          if (CallInst *call = dyn_cast<CallInst>(user)) {
            if (passedAsArg(func, call)) {
              errs() << "[DBG] " << func->getName()
                     << " is passed as argument\n";
            }
          }
        }
      } else if (Instruction *inst = dyn_cast<Instruction>(to_visit)) {
        errs() << "[*] " << *inst << "\n";

        // handle call
        if (CallInst *call = dyn_cast<CallInst>(inst)) {
          if (Function *func = call->getCalledFunction()) {
            dumpFunctionHeader(*func);

            // is external function, filter out
            if (func->isDeclaration()) {
              errs() << "[DBG] external function so removed\n";
              return true;
            }

            // TODO trace the return inst
          } else {
            Value *calledValue = call->getCalledOperand();
            worklist.push(calledValue);
          }
        } else {  // not call, go!
          // get operands
          for (auto &op : inst->operands()) {
            worklist.push(op.get());
          }
        }
      }
    }

    return filter;
  }

  vector<pair<Function *, Value *>> getVoidPointers(TypeGraph *tg) {
    vector<pair<Function *, Value *>> ret;

    for (auto &pair : tg->globalMap) {
      auto value = pair.first;
      auto typeset = pair.second;

      // skip function type
      if (typeset->isFunc) continue;

      if (typeset->size() == 1 && typeset->count("void*")) {
        ret.push_back({nullptr, value});
      }
    }

    for (auto &pair : tg->localMap) {
      auto scope = pair.first;
      for (auto &pair2 : *pair.second) {
        auto value = pair2.first;
        auto typeset = pair2.second;

        // skip function type
        if (typeset->isFunc) continue;

        if (typeset->size() == 1 && typeset->count("void*")) {
          ret.push_back({scope, value});
        }
      }
    }

    return ret;
  }

 public:
  PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {
    int successfully_inferred_cnt = 0;

    TypeSrc.setValue("di");
    TypeAnalyzer *analyzer = new TypeAnalyzer(&M);

    // initialize type graph with debug info
    auto tg = analyzer->init();

    // gather all values with void * type
    auto voidPointers = getVoidPointers(tg);  // filter out function types
    auto total_void_cnt = voidPointers.size();

    // run inference
    tg = analyzer->analyze();
    for (auto it = voidPointers.begin(); it != voidPointers.end(); ++it) {
      auto vp = *it;
      auto typeset = tg->get(vp.first, vp.second);

      if (!typeset) continue;

      if (typeset->size() > 1) {
        successfully_inferred_cnt++;
      } else {
        // tg->dumpType(vp.first, vp.second, typeset);
        // dump for debugging
        if (vp.second->hasName()) {
          auto shouldDel = lookupDUChain(vp.second);
          errs() << "\n";

          if (shouldDel) {
            total_void_cnt--;
            continue;
          }
        } else {  // anonymous
          total_void_cnt--;
          continue;
        }
      }

      // TODO: check if is used as indirect call
      // errs() << "[DBG] " << *vp.second << "\n";
      // errs() << "[DBG] users: \n";
      // for (auto user : vp.second->users()) {
      //     if (CallInst *call = dyn_cast<CallInst>(user)) {
      //         if (call->isIndirectCall()) {
      //             errs() << "\t(indirect call)" << *call << "\n";
      //             continue;
      //         }
      //     }
      //     errs() << "\t" << *user << "\n";
      // }
    }
    errs() << "\n[RESULT] number of void *: " << total_void_cnt << "\n";
    errs() << "[RESULT] number of successfully inferred: "
           << successfully_inferred_cnt << "\n";

    return PreservedAnalyses::all();
  }
};