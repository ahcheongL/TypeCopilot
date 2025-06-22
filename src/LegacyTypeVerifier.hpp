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

#include "LLVMHelper.hpp"

#include <regex>

using namespace llvm;
using namespace std;

// this pass is to match the legacy type with debug info to check the accuracy
class LegacyTypeVerifier : public PassInfoMixin<LegacyTypeVerifier> {
  private:
    int total_cnt = 0;
    int matched_cnt = 0;
    TypeHelper *tyHelper;
    DebugInfoHelper *diHelper;

    // find bitcast inst where each side are not i8* (not anycast)
    void find_abnormal_cast(Module &M) {
        for (auto &F : M) {
            for (auto &BB : F) {
                for (auto &inst : BB) {
                    if (auto bitcast = dyn_cast<BitCastInst>(&inst)) {
                        auto a = bitcast->getSrcTy();
                        auto b = bitcast->getDestTy();
                        auto a_name = tyHelper->getTypeName(a);
                        auto b_name = tyHelper->getTypeName(b);

                        // errs() << a_name << " " << b_name << "\n";
                        if (a_name != "i8*" && b_name != "i8*") {
                            // errs() << "[FOUND] " << inst << "\n";
                            // errs() << "bitcast: " << a_name << " -> " << b_name
                            //        << "\n";
                        }
                    }
                }
            }
        }
    }

    // FIXME
    map<string, string> type_trans_map = {
        {"ptr", "i8*"},
        {"bool", "i1"},
        {"short", "i16"},
        {"char", "i8"},
        {"int", "i32"},
        {"long", "i64"},
        {"long long", "i64"},
        {"unsigned char", "i8"},
        {"unsigned short", "i16"},
        {"unsigned long", "i64"},
        {"unsigned long long", "i64"},
        {"unsigned int", "i32"},

    };
    string di_to_ir_type(string &di_type) {
        string ir_type = di_type;

        // trim the ending multiple *
        int ptr_level = 0;
        while (ir_type.back() == '*') {
            ir_type.pop_back();
            ptr_level++;
        }

        // general types, in the table
        auto iter = type_trans_map.find(ir_type);
        if (iter != type_trans_map.end()) {
            ir_type = iter->second;
        } else {
            // di_type starts with "struct"
            if (ir_type.find("struct") == 0) {
                ir_type = "\%struct." + ir_type.substr(7);
            } else if (ir_type.find("enum") == 0) {
                ir_type = "i32";
            }
        }

        ir_type += string(ptr_level, '*');
        return ir_type;
    }

    // trim suffixing digits from ir types
    string trim_ir_suffix(string &ir_type) {
        regex pattern(R"((%struct\.[a-zA-Z_]\w*)\.\d+(\*?))");
        return regex_replace(ir_type, pattern, "$1$2");
    }

    bool match(string &ir_type, string &di_type) {
        if (ir_type == di_type) {
            return true;
        }

        if (ir_type == "i8" && di_type == "i1") {
            return true;
        }

        if (ir_type == "i64" && di_type == "i32") {
            return true;
        }

        return false;
    }

  public:
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {
        tyHelper = new TypeHelper();
        diHelper = new DebugInfoHelper();

        // globals
        // for (auto &global : M.globals()) {
        //     string ir_type, di_type;
        //     // IR global
        //     ir_type = tyHelper->getTypeName(global.getValueType());

        //     // Debug Info global
        //     SmallVector<DIGlobalVariableExpression *> di_global_exps;
        //     global.getDebugInfo(di_global_exps);
        //     if (di_global_exps.empty()) {
        //         continue;
        //     }
        //     for (auto di_global_exp : di_global_exps) {
        //         auto di_global = di_global_exp->getVariable();
        //         di_type = diHelper->getDITypeName(di_global->getType());
        //     }

        //     // compare
        //     total_cnt++;
        //     auto trans_di_type = di_to_ir_type(di_type);
        //     auto trimed_ir_type = trim_ir_suffix(ir_type);
        //     if (!match(trimed_ir_type, trans_di_type)) {
        //         errs() << "[ERROR] global type mismatch in " << global <<
        //         "\n"; errs() << "IR type: " << trimed_ir_type << " (" <<
        //         ir_type
        //                << ")\n";
        //         errs() << "DI type: " << trans_di_type << " (" << di_type
        //                << ")\n";
        //     } else {
        //         matched_cnt++;
        //     }
        // }

        for (auto &F : M) {
            Function *scope = dyn_cast<Function>(&F);

            // skip unnamed functions
            if (!scope->hasName())
                continue;

            // for (auto &arg : F.args()) {
            //     string ir_type;
            //     string di_type;
            //     ir_type = tyHelper->getTypeName(arg.getType());
            // }
            for (auto &BB : F) {
                for (auto &inst : BB) {
                    // resolve debug info
                    if (auto *call = dyn_cast<CallInst>(&inst)) {
                        auto call_func = call->getCalledFunction();
                        if (!call_func)
                            continue;
                        if (call_func->arg_size() < 2)
                            continue;

                        // check invoked function is intrinsic llvm debug
                        // function
                        if (call_func && call_func->isIntrinsic() &&
                            call_func->getName().startswith("llvm.dbg")) {

                            auto val = call->getArgOperand(0);
                            MetadataAsValue *mtv0 =
                                dyn_cast_or_null<MetadataAsValue>(val);
                            Metadata *mt0 = mtv0->getMetadata();
                            ValueAsMetadata *vmt =
                                dyn_cast_or_null<ValueAsMetadata>(mt0);
                            if (!vmt)
                                continue;
                            Value *real_val = vmt->getValue();

                            // get the second argument, which stores
                            // `DILocalVariable`
                            if (auto arg = call->getArgOperand(1)) {
                                auto metadata = dyn_cast<MetadataAsValue>(arg)
                                                    ->getMetadata();
                                auto di_value =
                                    dyn_cast<DILocalVariable>(metadata);

                                total_cnt++;
                                string ir_type =
                                    tyHelper->getTypeName(real_val->getType());
                                string di_type = diHelper->getDITypeName(
                                    di_value->getType());

                                auto trans_di_type = di_to_ir_type(di_type);
                                auto trimed_ir_type = trim_ir_suffix(ir_type);
                                if (!match(trimed_ir_type, trans_di_type)) {
                                    // errs() << "[ERROR] local type mismatch in"
                                    //        << F.getName() << ", " <<
                                    //        *real_val
                                    //        << "\n";
                                    // errs() << "IR type: " << trimed_ir_type
                                    //        << " (" << ir_type << ")\n";
                                    // errs() << "DI type: " << trans_di_type
                                    //        << " (" << di_type << ")\n";
                                } else {
                                    matched_cnt++;
                                }
                            }
                        }
                    }
                }
            }
        }

        errs() << "[RESULT] total count: " << total_cnt << "\n";
        errs() << "[RESULT] match count: " << matched_cnt << "\n";
        double coverage = (double)matched_cnt / total_cnt;
        errs() << "[RESULT] coverage: " << coverage << "\n";

        return PreservedAnalyses::all();
    }
};
