#pragma once

#include <llvm/IR/Constants.h>
#include <llvm/IR/DebugInfo.h>
#include <llvm/IR/DerivedTypes.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/InstrTypes.h>
#include <llvm/IR/Instruction.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Type.h>
#include <llvm/IR/Value.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/TypeName.h>
#include <llvm/Support/raw_ostream.h>

#include "LLVMHelper.hpp"
#include "TypeAlias.hpp"
#include "TypeGraph.hpp"
#include "WorkList.hpp"

using namespace std;
using namespace llvm;

extern cl::opt<string> TypeSrc;
extern cl::opt<bool>   DumpType;
extern cl::opt<bool>   Verbose;
extern cl::opt<bool>   Coverage;
extern cl::opt<bool>   Baseline;
extern cl::opt<bool>   TBAA;

class TypeAnalyzer {
 private:
  Module *module;

  // TypeGraph stores the results
  TypeGraph *tg;

  // Type Alias Rules
  TypeAlias *alias;

  WorkList *worklist;

  // helper classes
  LLVMHelper *llHelper;
  TypeHelper *tyHelper;

  void log(string msg) {
    if (Verbose.getValue()) errs() << msg;
  }

  void TBAAAccuracy() {
    int total_cnt = 0, valid_cnt = 0;

    // for multi-type set
    int any_pointer_cnt = 0, single_cnt = 0, multi_cnt = 0;

    auto groundtruth = new TypeGraph();
    auto tbaaHelper = new TBAAHelper();
    tbaaHelper->initialize(module, groundtruth);
    bool DEBUG = false;

    // validate
    for (auto &pair : groundtruth->globalMap) {
      total_cnt++;
      auto key = pair.first;
      auto groundtruth_type = pair.second;
      auto type = tg->get(nullptr, key);

      if (!type) {
        if (DEBUG) errs() << "[ERR] missing: " << *key << "\n";
        continue;
      }

      if (type->equalsBase(groundtruth_type)) {
        valid_cnt++;
      } else if (DEBUG) {
        errs() << "[ERR] mismatch: " << *key << "\n";
        errs() << "groundtruth: {";
        groundtruth_type->dump();
        errs() << "}, actual: {";
        type->dump();
        errs() << " }\n";
      }

      if (type->size() == 1) {
        single_cnt++;

        string str = type->at(0);
        if (str == "ptr") { continue; }

        if (str.length() >= 2 && str.substr(str.length() - 2) == "**") {
          continue;
        }

        if (groundtruth_type->size() == 1 &&
            groundtruth_type->count("any pointer")) {
          any_pointer_cnt++;
        }

      } else if (type->size() > 1) {
        multi_cnt++;
      }
    }

    for (auto &pair : groundtruth->localMap) {
      for (auto &pair2 : *pair.second) {
        total_cnt++;
        auto key = pair2.first;
        auto groundtruth_type = pair2.second;
        auto type = tg->get(pair.first, key);

        if (!type) {
          if (DEBUG) errs() << "[ERR] missing: " << *key << "\n";
          continue;
        }

        if (type->equalsBase(groundtruth_type)) {
          valid_cnt++;
        } else if (DEBUG) {
          errs() << "[ERR] mismatch: " << *key << "\n";
          errs() << "groundtruth: {";
          groundtruth_type->dump();
          errs() << "}, actual: {";
          type->dump();
          errs() << " }\n";
        }

        if (type->size() == 1) {
          single_cnt++;

          string str = type->at(0);
          if (str == "ptr") { continue; }

          if (str.length() >= 2 && str.substr(str.length() - 2) == "**") {
            continue;
          }

          if (groundtruth_type->size() == 1 &&
              groundtruth_type->count("any pointer")) {
            any_pointer_cnt++;
          }
        } else if (type->size() > 1) {
          multi_cnt++;
        }
      }
    }

    errs() << "[RESULT] total count: " << total_cnt << "\n";
    errs() << "[RESULT] valid count: " << valid_cnt << "\n";
    double coverage = (double)valid_cnt / total_cnt;
    errs() << "[RESULT] accuracy: " << coverage * 100 << "%\n";
    errs() << "[RESULT] any pointer count: " << any_pointer_cnt << "\n";
    errs() << "[RESULT] single type count: " << single_cnt << "\n";
  }

  /// real process function
  void process() {
    while (!worklist->empty()) {
      auto inst = worklist->pop();

      if (auto *cast = dyn_cast<CastInst>(inst)) {
        alias->processCast(cast->getFunction(), *cast);
      } else if (auto *load = dyn_cast<LoadInst>(inst)) {
        alias->processLoad(load->getFunction(), *load);
      } else if (auto *store = dyn_cast<StoreInst>(inst)) {
        alias->processStore(store->getFunction(), *store);
      } else if (auto *binop = dyn_cast<BinaryOperator>(inst)) {
        alias->processBinary(binop->getFunction(), *binop);
      } else if (auto *phi = dyn_cast<PHINode>(inst)) {
        alias->processPhi(phi->getFunction(), *phi);
      } else if (auto *gep = dyn_cast<GetElementPtrInst>(inst)) {
        alias->processFieldOf(gep->getFunction(), *gep);
      } else if (auto *cmp = dyn_cast<CmpInst>(inst)) {
        alias->processCmp(cmp->getFunction(), *cmp);
      } else if (auto *call = dyn_cast<CallInst>(inst)) {
        alias->processCall(call->getFunction(), *call);
      } else if (auto *select = dyn_cast<SelectInst>(inst)) {
        alias->processSelect(select->getFunction(), *select);
      }
    }
  }

 public:
  explicit TypeAnalyzer(Module *m) {
    module = m;
  }

  // ===================
  // initialize analyzer
  // ===================
  TypeGraph *init() {
    if (TypeSrc.getValue() == "mig") {
      log("[INFO] using migration instructions\n");
      llHelper = new MigrationHelper();
    } else if (TypeSrc.getValue() == "di") {
      log("[INFO] using debug info\n");
      DebugInfoHelper *diHelper = new DebugInfoHelper();

      if (!diHelper->hasDebugInfo(*module)) {
        errs() << "[ERR] no debug info found\n";
        return nullptr;
      }
      llHelper = diHelper;
    } else if (TypeSrc.getValue() == "tbaa") {
      log("[INFO] using TBAA metadata\n");
      TBAAHelper *tbaaHelper = new TBAAHelper();
      llHelper = tbaaHelper;
    } else if (TypeSrc.getValue() == "comb") {
      log("[INFO] using combination\n");
      CombHelper *combHelper = new CombHelper();

      if (!combHelper->hasDebugInfo(*module)) {
        errs() << "[ERR] no debug info found\n";
        return nullptr;
      }

      llHelper = combHelper;
    } else {
      errs() << "[ERR] unknown type source\n";
      exit(1);
    }

    // do initialization
    log("[INFO] initializing ...\n");

    tg = new TypeGraph();
    llHelper->initialize(module, tg);
    worklist = new WorkList(module);
    alias = new TypeAlias(module, tg, worklist, llHelper);

    if (Verbose.getValue()) tyHelper->count(module, tg);

    return tg;
  }

  // ==============
  // start analysis
  // ==============
  TypeGraph *analyze() {
    // do inference
    if (!Baseline.getValue()) process();

    if (Verbose.getValue()) tyHelper->count(module, tg);
    log("[INFO] done\n");

    // dump all types
    if (DumpType.getValue()) tg->dumpAllType();

    // calculate coverage
    if (Coverage.getValue()) { tg->coverage(module); }

    // calculate accuracy with TBAA as ground truth
    if (TBAA.getValue()) { TBAAAccuracy(); }
    return tg;
  }
};
