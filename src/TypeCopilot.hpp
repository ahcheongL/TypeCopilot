#pragma once

#include <llvm/IR/PassManager.h>

#include "TypeAnalyzer.hpp"

using namespace llvm;

class TypeCopilot : public PassInfoMixin<TypeCopilot> {

  public:
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
        auto analyzer = new TypeAnalyzer(&M);

        analyzer->init();
        analyzer->analyze();

        return PreservedAnalyses::all();
    }

    static bool isRequired() { return true; }
};