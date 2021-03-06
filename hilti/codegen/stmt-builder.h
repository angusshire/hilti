
#ifndef HILTI_CODEGEN_STMT_BUILDER_H
#define HILTI_CODEGEN_STMT_BUILDER_H

#include "../common.h"
#include "../passes/liveness.h"
#include "../statement.h"
#include "../visitor.h"

#include <hilti/autogen/instructions.h>

#include "codegen.h"
#include "common.h"

namespace hilti {
namespace codegen {

/// Visitor that generates the code for the execution of statemens. Note that
/// this class should not be used directly, it's used internally by CodeGen.
class StatementBuilder : public CGVisitor<>, public InstructionHelper {
public:
    /// Constructor.
    ///
    /// cg: The code generator to use.
    StatementBuilder(CodeGen* cg);
    virtual ~StatementBuilder();

    /// Generates the code for a statement.
    ///
    /// stmt: The statement.
    ///
    /// cleanup: If true, all temporaries creates are deleted after the
    /// statement.
    void llvmStatement(shared_ptr<Statement> stmt, bool cleanup = true);

    /// For a pair of expressions, returns the type of one expression into
    /// which the other one can be coerded. Tries either way. If both ways
    /// work, it's undefined which one is returned. If neither works, that's
    /// an error and execution will be aborted.
    ///
    /// This is mainly a helper function for code generation from one of the
    /// visit() methods.
    ///
    /// op1: The first expression.
    ///
    /// op2: The second expression.
    ///
    /// Returms: The type of either \c op1 (if \c op2 can be coerced into
    /// that) or \c op2 (if op1 can be coerced into that).
    shared_ptr<Type> coerceTypes(shared_ptr<Expression> op1, shared_ptr<Expression> op2) const;

    /// During visiting, return the currently processed statement.
    shared_ptr<Statement> currentStatement();

    // Computes the LLVM arguments for a HILTI function call.
    void prepareCall(shared_ptr<Expression> func, shared_ptr<Expression> args,
                     CodeGen::expr_list* call_params, bool before_call);

    // XXX Forwards to the liveness pass for the current statement.
    passes::Liveness::LivenessSets liveness();

protected:
    void preAccept(shared_ptr<ast::NodeBase> node) override;
    void postAccept(shared_ptr<ast::NodeBase> node) override;

    void visit(statement::Block* b) override;
    void visit(statement::Try* b) override;
    void visit(statement::try_::Catch* c) override;
    void visit(statement::ForEach* c) override;

    void visit(declaration::Function* f) override;
    void visit(declaration::Variable* v) override;
    void visit(declaration::Type* t) override;

// This is autogenerated and has the visits() for all the
// statement::instruction::*::* classes.
#include <hilti/autogen/instructions-stmt-builder.h>

private:
    std::list<shared_ptr<Statement>> _stmts;
};
}
}

#endif
