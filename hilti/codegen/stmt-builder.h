
#ifndef HILTI_CODEGEN_STMT_BUILDER_H
#define HILTI_CODEGEN_STMT_BUILDER_H

#include "../common.h"
#include "../visitor.h"

#include <autogen/instructions.h>

#include "common.h"
#include "codegen.h"

namespace hilti {
namespace codegen {

/// Visitor that generates the code for the execution of statemens. Note that
/// this class should not be used directly, it's used internally by CodeGen.
class StatementBuilder : public CGVisitor<>
{
public:
   /// Constructor.
   ///
   /// cg: The code generator to use.
   StatementBuilder(CodeGen* cg);
   virtual ~StatementBuilder();

   /// Generates the code for a statement.
   ///
   /// stmt: The statement.
   void llvmStatement(shared_ptr<Statement> stmt);

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

protected:
   void visit(statement::Block* b) override;

   void visit(declaration::Function* f);
   void visit(declaration::Variable* v);

   // This is autogenerated and has the visits() for all the
   // statement::instruction::*::* classes.
   #include <autogen/instructions-stmt-builder.h>

   void prepareCall(shared_ptr<Expression> func, shared_ptr<Expression> args, CodeGen::expr_list* call_params);

};

}
}

#endif
