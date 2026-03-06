#include <llvm/Passes/PassBuilder.h>
#include <llvm/Passes/PassPlugin.h>

#include "IdentifyProg.hpp"
#include "LegacyTypeVerifier.hpp"
#include "TBAAProfile.hpp"
#include "TypeCopilot.hpp"
#include "ValueDumper.hpp"
#include "VoidPtrCounter.hpp"

//-----------------------------------------------------------------------------
// Command Line Parameters
//-----------------------------------------------------------------------------

// get source file from commandline input
cl::opt<string> TypeSrc("type-src", cl::desc("Type source"),
                        cl::value_desc("type source"));
cl::opt<bool>   DumpType("dump-type", cl::desc("Dump all types"),
                         cl::value_desc("dump all types"));
cl::opt<bool> Verbose("verbose", cl::desc("Verbose"), cl::value_desc("verbose"),
                      cl::init(false));
cl::opt<bool> Coverage("coverage", cl::desc("Coverage"),
                       cl::value_desc("coverage"), cl::init(false));
cl::opt<bool> Baseline("baseline", cl::desc("Baseline"),
                       cl::value_desc("baseline"), cl::init(false));
cl::opt<bool> TBAA("tbaa-acc", cl::desc("TBAA as the benchmark"),
                   cl::value_desc("tbaa-acc"), cl::init(false));
cl::opt<bool> WL("wl", cl::desc("Enable Worklist"),
                 cl::value_desc("enable worklist"), cl::init(true));
cl::opt<string> OutputPath("output-path", cl::desc("Output path"),
                           cl::value_desc("output path"), cl::init(""));

//-----------------------------------------------------------------------------
// New PM Registration
//-----------------------------------------------------------------------------
llvm::PassPluginLibraryInfo getTypeCopilotPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "TypeCopilot", LLVM_VERSION_STRING,
          [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &MPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "typecopilot") {
                    MPM.addPass(TypeCopilot());
                    return true;
                  }

                  if (Name == "valuedumper") {
                    MPM.addPass(ValueDumper());
                    return true;
                  }

                  if (Name == "identifyprog") {
                    MPM.addPass(IdentifyProg());
                    return true;
                  }

                  if (Name == "verifytype") {
                    MPM.addPass(LegacyTypeVerifier());
                    return true;
                  }

                  if (Name == "voidptrcounter") {
                    MPM.addPass(VoidPtrCounter());
                    return true;
                  }

                  if (Name == "tbaaprofile") {
                    MPM.addPass(TBAAProfile());
                    return true;
                  }

                  return false;
                });
          }};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return getTypeCopilotPluginInfo();
}