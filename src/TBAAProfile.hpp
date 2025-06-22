#pragma once

#include "LLVMHelper.hpp"
#include "TypeGraph.hpp"
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Metadata.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/PassManager.h>

using namespace llvm;
using namespace std;

// this pass is to profile TBAA's statstic
class TBAAProfile : public PassInfoMixin<TBAAProfile> {
  private:
    bool hasTBAA(Instruction &I) {
        auto aamd = I.getAAMetadata();
        if (aamd.TBAA) {
            return true;
        }
        return false;
    }

    bool hasValidTBAA(Instruction &I) {
        auto aamd = I.getAAMetadata();
        if (aamd.TBAA) {
            // filter out any pointer type
            auto baseTy = dyn_cast<MDNode>(aamd.TBAA->getOperand(0));
            if (baseTy) {
                if (auto nameNode = dyn_cast<MDString>(baseTy->getOperand(0))) {
                    if (nameNode->getString().equals("any pointer")) {
                        return false;
                    }
                }
            }
            return true;
        }
        return false;
    }

    bool isLoadOrStore(Instruction &I) {
        return isa<LoadInst>(I) || isa<StoreInst>(I);
    }

  public:
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {
        int total_inst = 0;
        int tbaa_inst = 0;
        int valid_cnt = 0;

        auto groundtruth = new TypeGraph();
        auto tbaaHelper = new TBAAHelper();
        tbaaHelper->initialize(&M, groundtruth);

        errs() << "# TBAA: " << groundtruth->varSize() << "\n";

        return PreservedAnalyses::all();

        for (auto &F : M) {
            for (auto &F : M) {
                for (auto &BB : F) {
                    for (auto &I : BB) {
                        total_inst++;

                        if (hasTBAA(I)) {
                            tbaa_inst++;
                        }

                        // if (isLoadOrStore(I)) {
                        //     load_store_inst++;
                        //     if (hasTBAA(I)) {
                        //         tbaa_load_store_inst++;
                        //     }
                        //     if (hasValidTBAA(I)) {
                        //         valid_tbaa_load_store_inst++;
                        //     }
                        // }
                        if (hasValidTBAA(I)) {
                            valid_cnt++;
                        }
                    }
                }
            }

            errs() << "# Inst: " << total_inst << "\n";
            errs() << "# TBAA: " << tbaa_inst << "\n";
            // errs() << "% TBAA: "
            //        << format("%.2f", (double)tbaa_inst / total_inst * 100)
            //        << "%\n";
            // errs() << "---\n";
            // errs() << "# Any pointer: " << (tbaa_inst - valid_cnt) << "\n";
            errs() << "# Valid: " << valid_cnt << "\n";
            // errs() << "% Valid: "
            //        << format("%.2f", (double)valid_cnt / total_inst * 100)
            //        << "%\n";

            return PreservedAnalyses::all();
        }

        return PreservedAnalyses::all();
    }

    static bool isRequired() { return true; }
};