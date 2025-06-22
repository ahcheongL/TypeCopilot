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

#include <set>

using namespace llvm;
using namespace std;

// This is for issue 2.
class StructMatcher : public PassInfoMixin<StructMatcher> {

  private:
    int tot_struct = 0;
    int has_struct = 0;

    vector<StructType *> llvm_types;
    set<StringRef> type_names;

    bool has_type(StringRef &name) {
        if (type_names.find(name) != type_names.end()) {
            return true;
        }

        errs() << "Not found: " << name << "\n";

        return false;
    }

  public:
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
        // llvm's struct types
        llvm_types = M.getIdentifiedStructTypes();
        for (auto type : llvm_types) {
            auto name = type->getName();
            name.consume_front("struct.");

            if (name.contains(".")) {
                name = name.split(".").first;
            }
            type_names.insert(name);
        }

        // iterate debug info
        DebugInfoFinder finder;
        finder.processModule(M);
        set<StringRef> di_struct_types; // to strip off duplcates

        for (auto type : finder.types()) {
            // typedef
            // if (auto *derived = dyn_cast<DIDerivedType>(type)) {
            //     if (derived->getTag() == dwarf::DW_TAG_typedef) {
            //         auto base = derived->getBaseType();
            //         if (!base) {
            //             continue;
            //         }
            //         if (base->getTag() == dwarf::DW_TAG_structure_type) {
            //             auto name = derived->getName();
            //             if (name.empty()) {
            //                 continue;
            //             }
            //         }

            //         if (derived->getName().equals(s_name)) {
            //             structMap.insert({s, derived->getBaseType()});
            //             break;
            //         }
            //     }
            // }

            // struct
            if (auto *composite = dyn_cast<DICompositeType>(type)) {
                if (composite->getTag() == dwarf::DW_TAG_structure_type) {
                    auto name = composite->getName();
                    if (name.empty()) {
                        continue;
                    }

                    if (di_struct_types.find(name) != di_struct_types.end()) {
                        continue;
                    }

                    // check the struct
                    tot_struct++;
                    di_struct_types.insert(name);
                    if (has_type(name)) {
                        has_struct++;
                    }

                    // if (composite->getName().equals(s_name)) {
                    //     // empty elements, skip
                    //     if (composite->getElements().empty())
                    //         continue;

                    //     structMap.insert({s, composite});
                    //     break;
                    // }
                }
            }
        }

        // print out type names from debug info
        errs() << "--- BEGIN ---\n";
        for (auto type : di_struct_types) {
            errs() << type << "\n";
        }
        errs () << "--- END ---";

        errs() << "Total struct count: " << tot_struct << "\n";
        errs() << "Has llvm struct count: " << has_struct << "\n";

        return PreservedAnalyses::all();
    }

    static bool isRequired() { return true; }
};
