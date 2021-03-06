
#include <hilti/hilti-intern.h>

#include "../stmt-builder.h"
#include "hilti/autogen/instructions.h"

using namespace hilti;
using namespace codegen;

void StatementBuilder::visit(statement::instruction::flow::ReturnResult* i)
{
    auto func = current<declaration::Function>();
    auto rtype = ast::rtti::checkedCast<type::Function>(func->function()->type())->result()->type();
    auto op1 = cg()->llvmValue(i->op1(), rtype);
    cg()->llvmBuildInstructionCleanup();
    cg()->llvmReturn(func->function()->type()->result()->type(), op1, false);
}

static void _doVoidReturn(StatementBuilder* sbuilder)
{
    sbuilder->cg()->llvmBuildInstructionCleanup();

    auto func = sbuilder->current<declaration::Function>();

    // Check if we are in a hook. If so, we return a boolean indicating that
    // hook execution has not been stopped.
    if ( ! sbuilder->current<declaration::Hook>() )
        sbuilder->cg()->llvmReturn();
    else
        sbuilder->cg()->llvmReturn(0, sbuilder->cg()->llvmConstInt(0, 1));
}

void StatementBuilder::visit(statement::instruction::flow::ReturnVoid* i)
{
    _doVoidReturn(this);
}

#if 0

// Doesn't work:
//
// - if initial if statement doesn't trigger.
// - it would hang in loops as it doesn't track which stmtms is has already seen.
bool is_reachable(StatementBuilder* sbuilder, std::shared_ptr<Statement> s)
{
    if ( auto func = sbuilder->current<Function>() ) {
        if ( func->body()->firstNonBlock() == s )
            return true;
    }

    auto preds = sbuilder->cg()->hiltiModule()->cfg()->predecessors(s);

    for ( auto p : preds ) {
        if ( is_reachable(sbuilder, p) )
            return true;
    }

    return false;
}
#endif

void StatementBuilder::visit(statement::instruction::flow::BlockEnd* i)
{
    auto handler = cg()->topEndOfBlockHandler();

    if ( ! handler.first )
        return;

    if ( handler.second ) {
        // If we have a block to jump to on block end, go there.
        if ( ! cg()->builder()->GetInsertBlock()->getTerminator() ) {
            cg()->llvmBuildInstructionCleanup();
            cg()->llvmCreateBr(handler.second);
        }
    }

    else {
        // TODO: We catch this error here; can we do that in the validator?
        auto func = current<declaration::Function>();
        auto block = current<statement::Block>();

        auto rtype = func ? func->function()->type()->result()->type() : nullptr;

        if ( func && ! ast::rtti::isA<type::Void>(rtype) ) {
#if 0
            // Doesn't work currently, see above.
            if ( is_reachable(this, i->sharedPtr<Statement>()) ) {
                fatalError(i, ::util::fmt("function %s may finish without returning a value", func->function()->id()->pathAsString()));
                return;
            }
#endif

            // Return a dummy, we'll never get to this code.
            cg()->llvmReturn(rtype, cg()->llvmConstNull(cg()->llvmType(rtype)), false);
            return;
        }

        // Otherwise turn into a void return.
        _doVoidReturn(this);
    }
}

void StatementBuilder::prepareCall(shared_ptr<Expression> func, shared_ptr<Expression> args,
                                   CodeGen::expr_list* call_params, bool before_call)
{
    auto rtype = ast::rtti::tryCast<type::Reference>(func->type());
    auto ftype = ast::rtti::checkedCast<type::Function>(rtype ? rtype->argType() : func->type());
    auto expr = ast::rtti::checkedCast<expression::Constant>(args);
    auto params = ftype->parameters();
    auto p = params.begin();

    if ( expr && expr->isConstant() ) {
        // This is a short-cut to generate nicer code: if we have a constant
        // tuple, we use its element directly to avoid generating a struct first
        // just to then disassemble it again (LLVM should be able to optimize the
        // overhead in any case, but it's better readable this way.)

        for ( auto a : ast::rtti::tryCast<constant::Tuple>(expr->constant())->value() ) {
            call_params->push_back(a->coerceTo((*p)->type()));
            ++p;
        }
    }

    else {
        // Standard case: dissect the tuple struct.
        auto ttype = ast::rtti::tryCast<type::Tuple>(args->type());
        auto tval = cg()->llvmValue(args);

        int i = 0;
        auto p = params.begin();

        for ( shared_ptr<hilti::Type> t : ttype->typeList() ) {
            llvm::Value* val = cg()->llvmExtractValue(tval, i++);
            auto expr = shared_ptr<Expression>(new expression::CodeGen(t, val));
            call_params->push_back(expr->coerceTo(((*p)->type())));
            ++p;
        }
    }

    // Add default values.
    while ( p != params.end() ) {
        auto def = (*p++)->default_();

        if ( ! def )
            break;

        call_params->push_back(def);
    }

    // Must come last as it will change the next llvmCall()
    if ( before_call )
        cg()->setInstructionCleanupAfterCall();
}

void StatementBuilder::visit(statement::instruction::flow::CallVoid* i)
{
    auto func = cg()->llvmValue(i->op1());
    auto ftype = ast::rtti::tryCast<type::Function>(i->op1()->type());

    CodeGen::expr_list params;
    prepareCall(i->op1(), i->op2(), &params, true);
    cg()->llvmCall(func, ftype, params);
}

void StatementBuilder::visit(statement::instruction::flow::CallResult* i)
{
    auto func = cg()->llvmValue(i->op1());
    auto ftype = ast::rtti::tryCast<type::Function>(i->op1()->type());

    CodeGen::expr_list params;
    prepareCall(i->op1(), i->op2(), &params, true);
    auto result = cg()->llvmCall(func, ftype, params);

    auto var = ast::rtti::checkedCast<expression::Variable>(i->target());

    if ( ast::rtti::isA<type::Any>(ftype->result()->type()) ) {
        auto ttype = i->target()->type();

        if ( ftype->callingConvention() == type::function::HILTI_C ) {
            auto casted =
                builder()->CreateBitCast(result, cg()->llvmTypePtr(cg()->llvmType(ttype)));
            result = builder()->CreateLoad(casted);
        }

        else
            result = cg()->builder()->CreateBitCast(result, cg()->llvmType(ttype));
    }

    if ( (! ast::rtti::isA<variable::Local>(var->variable())) ||
         cg()->hiltiModule()->liveness()->liveOut(i->sharedPtr<Statement>(), i->target()) )
        cg()->llvmStore(i->target(), result, false);

    cg()->llvmDebugPrint("hilti-trace", "end-of-call-result");
}

void StatementBuilder::visit(statement::instruction::flow::CallCallableVoid* i)
{
    auto ctype = ast::rtti::tryCast<type::Callable>(referencedType(i->op1()));

    auto op1 = cg()->llvmValue(i->op1());

    CodeGen::expr_list params;

    if ( i->op2() )
        prepareCall(i->op1(), i->op2(), &params, true);

    cg()->llvmCallableRun(ctype, op1, params);
}

void StatementBuilder::visit(statement::instruction::flow::CallCallableResult* i)
{
    auto ctype = ast::rtti::tryCast<type::Callable>(referencedType(i->op1()));

    auto op1 = cg()->llvmValue(i->op1());

    CodeGen::expr_list params;

    if ( i->op2() )
        prepareCall(i->op1(), i->op2(), &params, true);

    auto result = cg()->llvmCallableRun(ctype, op1, params);

    cg()->llvmStore(i->target(), result);
}

void StatementBuilder::visit(statement::instruction::flow::Yield* i)
{
    auto fiber = cg()->llvmCurrentFiber();
    cg()->llvmFiberYield(fiber);
}

void StatementBuilder::visit(statement::instruction::flow::YieldUntil* i)
{
    auto fiber = cg()->llvmCurrentFiber();
    cg()->llvmFiberYield(fiber, i->op1()->type(), cg()->llvmValue(i->op1()));
}

void StatementBuilder::visit(statement::instruction::flow::IfElse* i)
{
    auto btype = shared_ptr<Type>(new type::Bool());
    auto op1 = cg()->llvmValue(i->op1(), btype);
    auto op2 = cg()->llvmValue(i->op2());
    auto op3 = cg()->llvmValue(i->op3());

    auto op2_bb = llvm::cast<llvm::BasicBlock>(op2);
    auto op3_bb = llvm::cast<llvm::BasicBlock>(op3);

    cg()->llvmBuildInstructionCleanup();

    cg()->builder()->CreateCondBr(op1, op2_bb, op3_bb);
}

void StatementBuilder::visit(statement::instruction::flow::Jump* i)
{
    auto op1 = cg()->llvmValue(i->op1());
    auto op1_bb = llvm::cast<llvm::BasicBlock>(op1);

    cg()->llvmBuildInstructionCleanup();
    cg()->builder()->CreateBr(op1_bb);
}

void StatementBuilder::visit(statement::instruction::flow::Switch* i)
{
    auto op1 = cg()->llvmValue(i->op1());
    auto default_ = llvm::cast<llvm::BasicBlock>(cg()->llvmValue(i->op2()));
    auto a1 = ast::rtti::tryCast<expression::Constant>(i->op3());
    auto a2 = ast::rtti::tryCast<constant::Tuple>(a1->constant());

    std::list<std::pair<llvm::Value*, llvm::BasicBlock*>> alts;

    bool all_const = true;

    for ( auto c : a2->value() ) {
        auto c1 = ast::rtti::tryCast<expression::Constant>(c);
        auto c2 = ast::rtti::tryCast<constant::Tuple>(c1->constant());

        auto v = c2->value();
        auto j = v.begin();
        auto val = cg()->llvmValue((*j++)->coerceTo(i->op1()->type()));
        auto block = llvm::cast<llvm::BasicBlock>(cg()->llvmValue(*j++));

        if ( ! llvm::isa<llvm::Constant>(val) )
            all_const = false;

        alts.push_back(std::make_pair(val, block));
    }

    if ( all_const && ast::rtti::isA<type::Integer>(i->op1()->type()) ) {
        cg()->llvmBuildInstructionCleanup();

        // We optimize for constant integers here, for which LLVM directly
        // provides a switch statement.
        auto switch_ = cg()->builder()->CreateSwitch(op1, default_);

        for ( auto a : alts ) {
            auto c = llvm::cast<llvm::ConstantInt>(a.first);
            assert(c);
            switch_->addCase(c, a.second);
        }
    }

    else {
        // In all other cases, we build an if-else chain using the type's
        // standard comparision operator. However, the fact that we need
        // cleanup tmps before diverting control flow makes this a bit tricky
        // and we do it in teps: the if-else chain only determines which
        // block to jump to; then we cleanup tmps; and then we do the branch.
        //
        // TODO: We're doing the indirect branch with an integer and switch,
        // instead of using LLVM's indirect brach statement[1] because
        // there's evidence[2] that the JIT might not like that ...
        //
        // [1] http://blog.llvm.org/2010/01/address-of-label-and-indirect-branches.html
        // [2] http://llvm.org/bugs/show_bug.cgi?id=6744

        auto done = cg()->newBuilder("switch-done");

        auto cmp = cg()->makeLocal("switch-cmp", builder::boolean::type());

        auto destination = cg()->llvmCreateAlloca(cg()->llvmTypeInt(64));
        cg()->llvmCreateStore(cg()->llvmConstInt(0, 64), destination); // Zero for default.

        int n = 1;
        for ( auto a : alts ) {
            cg()->llvmInstruction(cmp, instruction::operator_::Equal, i->op1(),
                                  builder::codegen::create(i->op1()->type(), a.first));
            auto next_block = cg()->newBuilder("switch-chain");
            auto found = cg()->newBuilder("switch-match");
            cg()->builder()->CreateCondBr(cg()->llvmValue(cmp), found->GetInsertBlock(),
                                          next_block->GetInsertBlock());

            cg()->pushBuilder(found);
            cg()->llvmCreateStore(cg()->llvmConstInt(n++, 64), destination);
            cg()->builder()->CreateBr(done->GetInsertBlock());
            cg()->popBuilder();

            cg()->pushBuilder(next_block);
        }

        cg()->builder()->CreateBr(done->GetInsertBlock());

        cg()->pushBuilder(done);

        cg()->llvmBuildInstructionCleanup();

        // Do the indirect branch.
        auto switch_ =
            cg()->builder()->CreateSwitch(cg()->builder()->CreateLoad(destination), default_);

        n = 1;
        for ( auto a : alts )
            switch_->addCase(cg()->llvmConstInt(n++, 64), a.second);

        cg()->popBuilder();
    }
}

void StatementBuilder::visit(statement::instruction::flow::DispatchUnion* i)
{
    auto default_ = llvm::cast<llvm::BasicBlock>(cg()->llvmValue(i->op2()));
    auto a1 = ast::rtti::tryCast<expression::Constant>(i->op3());
    auto a2 = ast::rtti::tryCast<constant::Tuple>(a1->constant());

    std::list<std::pair<llvm::Value*, llvm::BasicBlock*>> alts;

    for ( auto c : a2->value() ) {
        auto c1 = ast::rtti::tryCast<expression::Constant>(c);
        auto c2 = ast::rtti::tryCast<constant::Tuple>(c1->constant());

        auto v = c2->value();
        auto j = v.begin();
        auto type = cg()->llvmValue((*j++));
        auto block = llvm::cast<llvm::BasicBlock>(cg()->llvmValue(*j++));

        alts.push_back(std::make_pair(type, block));
    }

    // TODO: Same todo here as above with the Switch statement regarding
    // indirecbr.

    auto done = cg()->newBuilder("dispatch-done");

    auto addr = cg()->llvmValueAddress(i->op1());
    CodeGen::value_list args = {cg()->llvmRtti(i->op1()->type()),
                                cg()->builder()->CreateBitCast(addr, cg()->llvmTypePtr())};

    auto union_type = cg()->llvmCallC("__hlt_union_type", args, false, false);

    auto destination = cg()->llvmCreateAlloca(cg()->llvmTypeInt(64));
    cg()->llvmCreateStore(cg()->llvmConstInt(0, 64), destination); // Zero for default.

    int n = 1;

    for ( auto a : alts ) {
        CodeGen::value_list args = {union_type, a.first};
        auto match = cg()->llvmCallC("__hlt_type_equal", args, false, false);
        auto next_block = cg()->newBuilder("dispatch-chain");
        auto found = cg()->newBuilder("dispatch-match");
        cg()->builder()->CreateCondBr(match, found->GetInsertBlock(), next_block->GetInsertBlock());

        cg()->pushBuilder(found);
        cg()->llvmCreateStore(cg()->llvmConstInt(n++, 64), destination);
        cg()->builder()->CreateBr(done->GetInsertBlock());
        cg()->popBuilder();

        cg()->pushBuilder(next_block);
    }

    cg()->builder()->CreateBr(done->GetInsertBlock());

    cg()->pushBuilder(done);

    cg()->llvmBuildInstructionCleanup();

    // Do the indirect branch.
    auto switch_ =
        cg()->builder()->CreateSwitch(cg()->builder()->CreateLoad(destination), default_);

    n = 1;
    for ( auto a : alts )
        switch_->addCase(cg()->llvmConstInt(n++, 64), a.second);

    cg()->popBuilder();
}
