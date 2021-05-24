//
// Created by machiry on 5/10/17.
//

#ifndef PROJECT_DEFIOCTLINSTVISITOR_H
#define PROJECT_DEFIOCTLINSTVISITOR_H

#include <set>
#include "llvm/Pass.h"
//#include "dsa/DSGraph.h"
//#include "dsa/DataStructure.h"
#include "llvm/Analysis/AliasSetTracker.h"
#include "llvm/IR/InstVisitor.h"
#include "llvm/IR/CFG.h"
//#include "../../RangeAnalysis/include/RangeAnalysis.h"

using namespace llvm;
namespace IOCTL_CHECKER {
    class DefIoctlInstVisitor : public InstVisitor<DefIoctlInstVisitor> {
    public:

        Function *targetFunction;

        // All instructions whose result depend on the value
        // value which is derived from cmd arg value.
        std::set<Value*> allCmdInstrs;
        // similar to cmd arg, this is for use arg.
        std::set<Value*> allArgInstrs;
        // value of the cmd, for
        // which the current branch belongs to
        // by default this will be nullptr
        Value *currCmdValue;
        // call stack.
        std::vector<Value*> callStack;

        std::set<BasicBlock*> visitBBs;

        // map that stores the actual values passed by the caller,
        // this is useful in determining the type of argument.
        std::map<Value*, Value*> callerArgs;

        // Range analysis results.
        //RangeAnalysis *range_analysis;

        // Pointer to the visitor which called.
        DefIoctlInstVisitor *calledVisitor;

        unsigned long curr_func_depth;


        DefIoctlInstVisitor(Function *targetFunc, std::set<int> &cmdArg, std::set<int> &uArg, std::map<unsigned, Value*> &callerArguments,
                            std::vector<Value*> &calledStack, DefIoctlInstVisitor *calledVisitor, unsigned long curr_func_depth) {
            // Initialize all values.
            _super = static_cast<InstVisitor *>(this);
            this->targetFunction = targetFunc;
            unsigned int farg_no=0;
            for(Function::arg_iterator farg_begin = targetFunc->arg_begin(), farg_end = targetFunc->arg_end();
                farg_begin != farg_end; farg_begin++) {
                Value *currfArgVal = &(*farg_begin);
                if(cmdArg.find(farg_no) != cmdArg.end()) {
                    allCmdInstrs.insert(currfArgVal);
                }
                if(uArg.find(farg_no) != uArg.end()) {
                    allArgInstrs.insert(currfArgVal);
                }
                if(callerArguments.find(farg_no) != callerArguments.end()) {
                    this->callerArgs[currfArgVal] = callerArguments[farg_no];
                }
                farg_no++;
            }

            this->calledVisitor = calledVisitor;

            this->callStack.insert(this->callStack.end(), calledStack.begin(), calledStack.end());
            //this->range_analysis = curr_range_analysis;
            this->currCmdValue = nullptr;
            this->curr_func_depth = curr_func_depth;
        }

        bool isVisited(BasicBlock *currBB) {
            return this->visitBBs.find(currBB) != this->visitBBs.end();
        }

        void addBBToVisit(BasicBlock *currBB) {
            if(this->visitBBs.find(currBB) == this->visitBBs.end()) {
                this->visitBBs.insert(currBB);
            }
        }

        bool isCmdAffected(Value *targetValue) {
            if(allCmdInstrs.find(targetValue) == allCmdInstrs.end()) {
                return allCmdInstrs.find(targetValue->stripPointerCasts()) != allCmdInstrs.end();
            }
            return true;
        }

        bool isArgAffected(Value *targetValue) {
            if(allArgInstrs.find(targetValue) == allArgInstrs.end()) {
                return allArgInstrs.find(targetValue->stripPointerCasts()) != allArgInstrs.end();
            }
            return true;
        }

        virtual void visit(Instruction &I) {
#ifdef DEBUG_INSTR_VISIT
            dbgs() << "Visiting instruction:";
            I.print(dbgs());
            dbgs() << "\n";
#endif

            // if this is not a call instruction.
            if(!dyn_cast<CallInst>(&I) && !dyn_cast<PHINode>(&I)) {
                for (unsigned int i = 0; i < I.getNumOperands(); i++) {
                    Value *currValue = I.getOperand(i);
                    if (currValue != nullptr) {
                        Value *strippedValue = currValue->stripPointerCasts();
                        if (allCmdInstrs.find(currValue) != allCmdInstrs.end() ||
                            allCmdInstrs.find(strippedValue) != allCmdInstrs.end()) {
                            // insert only if this is not present.
                            if (allCmdInstrs.find(&I) == allCmdInstrs.end()) {
                                allCmdInstrs.insert(&I);
                            }
                        }
                        if (allArgInstrs.find(currValue) != allArgInstrs.end() ||
                            allArgInstrs.find(strippedValue) != allArgInstrs.end()) {
                            // only insert if this instruction is not present.
                            if (allArgInstrs.find(&I) == allArgInstrs.end()) {
                                allArgInstrs.insert(&I);
                            }
                        }

                    }

                }
            }
            this->_super->visit(I);
        }

        // visitor functions.

        virtual void visitCallInst(CallInst &I);

        //virtual void visitICmpInst(ICmpInst &I);



        bool visitBB(BasicBlock *BB);

        // main analysis function.
        void analyze();

        bool handleCmdSwitch(SwitchInst *targetSwitchInst);

        //bool handleCmdCond(BranchInst *I, std::set<BasicBlock*> &totalVisited);

        void visitAllBBs(BasicBlock *startBB, std::set<BasicBlock*> &visitedBBs);
    private:
        InstVisitor *_super;
        //void getArgPropogationInfo(CallInst *I, std::set<int> &cmdArg, std::set<int> &uArg, std::map<unsigned, Value*> &callerArgInfo);

        //bool isInstrToPropogate(Instruction *I);
    };
}

#endif //PROJECT_DEFIOCTLINSTVISITOR_H
