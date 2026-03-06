#pragma once

#include <llvm/ADT/Hashing.h>
#include <llvm/BinaryFormat/Dwarf.h>
#include <llvm/IR/DebugInfo.h>
#include <llvm/IR/DebugInfoMetadata.h>
#include <llvm/IR/DerivedTypes.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/GlobalValue.h>
#include <llvm/IR/InstrTypes.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/PassManager.h>
#include <llvm/IR/ValueSymbolTable.h>
#include <llvm/Pass.h>
#include <llvm/PassRegistry.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/raw_ostream.h>

#include <unordered_set>

using namespace llvm;
using namespace std;

class IdentifyProg : public PassInfoMixin<IdentifyProg> {
 public:
  PreservedAnalyses run(Module &module, ModuleAnalysisManager &FAM) {
    // getPointerElementType() is deprecated.

    // std::unordered_set<PHINode *> allphis;
    // for (Module::iterator fi = module.begin(), fe = module.end(); fi != fe;
    //      ++fi) {
    //   Function *func = dyn_cast<Function>(fi);
    //   if (func->isDeclaration() || func->isIntrinsic() || (!func->hasName()))
    //     continue;

    //   for (Function::iterator bi = func->begin(), be = func->end(); bi != be;
    //        ++bi) {
    //     BasicBlock *bb = dyn_cast<BasicBlock>(bi);
    //     for (BasicBlock::iterator ii = bb->begin(), ie = bb->end(); ii != ie;
    //          ++ii) {
    //       if (PHINode *phi = dyn_cast<PHINode>(ii)) {
    //         PointerType *ty = dyn_cast<PointerType>(phi->getType());
    //         Type        *base = nullptr;
    //         while (ty) {
    //           base = ty->getPointerElementType();
    //           ty = dyn_cast<PointerType>(base);
    //         }
    //         if (IntegerType *inte = dyn_cast_or_null<IntegerType>(base)) {
    //           if (inte->getBitWidth() == 8) { allphis.insert(phi); }
    //         }
    //       }
    //     }
    //   }
    // }

    // for (auto phi : allphis) {
    //   Value *op;
    //   for (unsigned int i = 0; i < phi->getNumIncomingValues(); ++i) {
    //     op = phi->getIncomingValue(i);
    //     if (ConstantExpr *cxpr = dyn_cast<ConstantExpr>(op)) {
    //       op = cxpr->getAsInstruction();
    //     }

    //     if (BitCastInst *castinst = dyn_cast<BitCastInst>(op)) {
    //       Value *from = castinst->getOperand(0);
    //       Type  *fromtype = from->getType();

    //       PointerType *ty = dyn_cast<PointerType>(fromtype);
    //       Type        *base = fromtype;
    //       while (ty) {
    //         base = ty->getPointerElementType();
    //         ty = dyn_cast<PointerType>(base);
    //       }
    //       if (StructType *st = dyn_cast<StructType>(base)) {
    //         if (st->hasName() &&
    //             !(st->getName().starts_with("struct.list_head"))) {
    //           errs() << *phi << '\n' << phi->getFunction()->getName() <<
    //           "\n\n";
    //         }
    //       }
    //     }
    //   }
    // }

    /*
    for (Module::iterator fi = module.begin(), fe = module.end(); fi != fe;
         ++fi) {
      Function *func = dyn_cast<Function>(fi);
      if (func->isDeclaration() || func->isIntrinsic() ||
    (!func->hasName())) continue;

      // if (func->getName().starts_with(bpf_runner)) {
      if (func->getName().str() == bpf_runner) {

                                                                                                                                                                                                                                                  13:19:26 [36/467]
        bpf_runner_funcs[func] = 0;
        //   errs() << "found bpf function:" << func->getName() << "\n";
        findCallerIter(func, 0);
        //   break;
      }
    }


    for (Module::iterator fi = module.begin(), fe = module.end(); fi != fe;
         ++fi) {
      Function *func = dyn_cast<Function>(fi);
      if (func->isDeclaration() || func->isIntrinsic() ||
    (!func->hasName())) continue; for (Function::iterator bi =
    func->begin(), be = func->end(); bi != be;
           ++bi) {
        BasicBlock *bb = dyn_cast<BasicBlock>(bi);
        for (BasicBlock::iterator ii = bb->begin(), ie = bb->end(); ii !=
    ie;
             ++ii) {
          if (CallInst *ci = dyn_cast<CallInst>(ii)) {
            Function *callee = getCalleeFunctionDirect(ci);
            if (callee && callee->hasName()) {
              for (auto func_arg : bpf_runner_funcs) {
                Function *interest_func = func_arg.first;
                unsigned int arg_pos = func_arg.second;

                if (callee->getName().starts_with(interest_func->getName()))
    {
                  // backtrace the argument;
                  // errs() << "possible callinst: " << *ci << "\n";
                  Value *v = ci->getArgOperand(arg_pos);
                  traceValueInParent(v);
                }
              }
            }
          }
        }
      }
      errs() << "\n\n------------------------Collected "
              "function-------------------------- \n";
    for (auto fa : bpf_runner_funcs) {
      errs() << fa.first->getName() << "\t" << fa.second << "\n";
    }

    errs()
        << "\n\n---------------------Prog global
    variable--------------------\n";

    for (auto *gv : interesting_gvs) {
      errs() << *gv;
      for (auto u : gv->users()) {
        traceValueInParent(u);
      }
    }

    // print final result
    errs()
        << "\n\n-----------------------Final result-------------------------
    \n"; for (auto sf : interesting_set) { errs() << "Struct type: " <<
    sf.type->getStructName()
             << "\t index: " << sf.field << '\n';
      const llvm::DataLayout &TD = module.getDataLayout();
      const llvm::StructLayout *SL = TD.getStructLayout(sf.type);
      errs() << "whole struct size: " << SL->getSizeInBytes();
      errs() << "\t offset: " << SL->getElementOffset(sf.field) << "\n\n";
    }
      */

    return PreservedAnalyses::all();
  }
};
