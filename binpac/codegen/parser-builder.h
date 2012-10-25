
#ifndef BINPAC_CODEGEN_PARSER_BUILDER_H
#define BINPAC_CODEGEN_PARSER_BUILDER_H

#include <ast/visitor.h>

#include "common.h"
#include "cg-visitor.h"

namespace binpac {

namespace type { namespace unit { namespace item { class Field; } } }

namespace codegen {

class ParserState;

/// Generates code to parse input according to a grammar.
class ParserBuilder : public CGVisitor<shared_ptr<hilti::Expression>, shared_ptr<type::unit::item::Field>>
{
public:
    ParserBuilder(CodeGen* cg);
    virtual ~ParserBuilder();

    /// Returns the type of the currently parsed unit. The method must only
    /// be called when parsing is in progress.
    shared_ptr<type::Unit> unit() const;

    /// Generates the function to parse input according to a unit's grammar.
    ///
    /// u: The unit to generate the parser for.
    ///
    /// Returns: The generated HILTI function with the parsing code.
    shared_ptr<hilti::Expression> hiltiCreateParseFunction(shared_ptr<type::Unit> u);

    /// Generates the externally visible functions for parsing a unit type.
    ///
    /// u: The unit type to export via functions.
    void hiltiExportParser(shared_ptr<type::Unit> unit);

    /// Generates the implementation of unit-embedded hooks.
    ///
    /// u: The unit type to generate the hooks for.
    void hiltiUnitHooks(shared_ptr<type::Unit> unit);

    // Returns the HILTI struct type for a unit's parse object.
    shared_ptr<hilti::Type> hiltiTypeParseObject(shared_ptr<type::Unit> unit);

    /// Adds an external implementation of a unit hook.
    ///
    /// id: The hook's ID (full path).
    ///
    /// hook: The hook itself.
    void hiltiDefineHook(shared_ptr<ID> id, shared_ptr<Hook> hook);

    /// Generates code to execute the hooks associated with an unit item.
    /// This must only be called while a unit is being parsed.
    ///
    /// f: The field.
    void hiltiRunFieldHooks(shared_ptr<type::unit::Item> item);

    /// Returns a HILTI expression referencing the current parser object
    /// (assuming parsing is in process; if not aborts());
    shared_ptr<hilti::Expression> hiltiSelf();

protected:
    /// Returns the current parsing state.
    shared_ptr<ParserState> state() const;

    /// Pushes a new parsing state onto the stack.
    void pushState(shared_ptr<ParserState> state);

    /// Pops the current parsing state from the stack.
    void popState();

    void visit(constant::Address* a) override;
    void visit(constant::Bitset* b) override;
    void visit(constant::Bool* b) override;
    void visit(constant::Double* d) override;
    void visit(constant::Enum* e) override;
    void visit(constant::Integer* i) override;
    void visit(constant::Interval* i) override;
    void visit(constant::Network* n) override;
    void visit(constant::Port* p) override;
    void visit(constant::String* s) override;
    void visit(constant::Time* t) override;

    void visit(ctor::Bytes* b) override;
    void visit(ctor::RegExp* r) override;

    void visit(production::Boolean* b) override;
    void visit(production::ChildGrammar* c) override;
    void visit(production::Counter* c) override;
    void visit(production::Epsilon* e) override;
    void visit(production::Literal* l) override;
    void visit(production::LookAhead* l) override;
    void visit(production::NonTerminal* n) override;
    void visit(production::Sequence* s) override;
    void visit(production::Switch* s) override;
    void visit(production::Terminal* t) override;
    void visit(production::Variable* v) override;
    void visit(production::While* w) override;
    void visit(production::Loop* l) override;

    void visit(type::Address* a) override;
    void visit(type::Bitset* b) override;
    void visit(type::Bool* b) override;
    void visit(type::Bytes* b) override;
    void visit(type::Double* d) override;
    void visit(type::Enum* e) override;
    void visit(type::Integer* i) override;
    void visit(type::Interval* i) override;
    void visit(type::List* l) override;
    void visit(type::Network* n) override;
    void visit(type::Port* p) override;
    void visit(type::Set* s) override;
    void visit(type::String* s) override;
    void visit(type::Time* t) override;
    void visit(type::Unit* u) override;
    void visit(type::unit::Item* i) override;
    void visit(type::unit::item::Field* f) override;
    void visit(type::unit::item::field::Constant* c) override;
    void visit(type::unit::item::field::Ctor* r) override;
    void visit(type::unit::item::field::Switch* s) override;
    void visit(type::unit::item::field::AtomicType* t) override;
    void visit(type::unit::item::field::Unit* t) override;
    void visit(type::unit::item::field::switch_::Case* c) override;
    void visit(type::unit::item::Variable* v) override;
    void visit(type::unit::item::Property* p) override;
    void visit(type::unit::item::GlobalHook* h) override;
    void visit(type::Vector* v) override;

private:
    // TODO: This should be defined in the HILTI namespace.
    typedef std::list<shared_ptr<hilti::Expression>> hilti_expression_list;

    // Pushes an empty parse function with the right standard signature.
    //
    // Returns: An expression referencing the function.
    shared_ptr<hilti::Expression> _newParseFunction(const string& name, shared_ptr<type::Unit> unit);

    // Allocates and initializes a new parse object.
    shared_ptr<hilti::Expression> _allocateParseObject(shared_ptr<Type> unit, bool store_in_self);

    // Initializes the current parse object before starting the parsing
    // process.
    void _prepareParseObject(const hilti_expression_list& params);

    // Finalizes the current parser when the parsing process has finished.
    void _finalizeParseObject();

    // Called just before a production is being parsed.
    void _startingProduction(shared_ptr<Production> p, shared_ptr<type::unit::item::Field> field);

    // Called just after a production has been parsed.
    void _finishedProduction(shared_ptr<Production> p);

    // Callen when parsing a production leads to a new value to be assigned
    // to a user-visible field of the current parse object. This method is
    // doing the actual assignment and triggering the corresponding hook. If
    // value is nullptr, the fields current value is taken to trigger the
    // hook.
    void _newValueForField(shared_ptr<type::unit::item::Field> field, shared_ptr<hilti::Expression> value);

    // Creates the host-facing parser function. If sink is true, we generate
    // a slightly different version for internal use with sinks.
    shared_ptr<hilti::Expression> _hiltiCreateHostFunction(shared_ptr<type::Unit> unit, bool sink);

    // Creates the init function that registers a parser with the binpac runtime.
    void _hiltiCreateParserInitFunction(shared_ptr<type::Unit> unit, shared_ptr<hilti::Expression> parse_host, shared_ptr<hilti::Expression> parse_sink);

    // Returns the BinPAC::Parser instance for a unit.
    shared_ptr<hilti::Expression> _hiltiParserDefinition(shared_ptr<type::Unit> unit);

    // Prints the given message to the binpac debug stream.
    void _hiltiDebug(const string& msg);

    // Prints the given message to the binpac verbose debug stream.
    void _hiltiDebugVerbose(const string& msg);

    // Prints the given token to binpac-verbose.
    void _hiltiDebugShowToken(const string& tag, shared_ptr<hilti::Expression> token);

    // Prints the upcoming input bytes to binpac-verbose.
    void _hiltiDebugShowInput(const string& tag, shared_ptr<hilti::Expression> cur);

    // Executes a hook. <id> is the full path to the hooked element,
    // including the module. \a foreach must be true if this is a \c forach
    // hook. \a dolllardollar is the value for the \a $$ identifier within
    // the hook, if it takes one (or null). If \a foreach is true, returns a
    // boolean expression that is true if the hook has called "hook.stop
    // true". If \a foreach is false, returns null.
    shared_ptr<hilti::Expression> _hiltiRunHook(shared_ptr<ID> id, bool foreach, shared_ptr<hilti::Expression> dollardollar = nullptr);

    // Defines a hook's implementation. <id> is the full path to the hooked
    // element, including the module. <forach> is true if this is a \c
    // &foreach hook. The ID of \a hook is ignored. \a dollardollar, if
    // given, is the type for the \a $$ identifier within the hook, if it
    // takes one.
    void _hiltiDefineHook(shared_ptr<ID> id, bool foreach, shared_ptr<type::Unit> unit, shared_ptr<Statement> block, shared_ptr<Type> dollardollar = nullptr, int priority = 0);

    // Returns the full path ID for the hook referecing a unit item.
    shared_ptr<ID> _hookForItem(shared_ptr<type::Unit>, shared_ptr<type::unit::Item> item, bool foreach, bool private_);

    // Returns the full path ID for the hook referecing a unit-global hook.
    shared_ptr<ID> _hookForUnit(shared_ptr<type::Unit>, const string& name);

    // Computes the canonical hook name, given the full path. The returned
    // boolean indicates whether the hook is a local one (i.e., within the
    // same module; true) or cross-module (false).
    std::pair<bool, string> _hookName(const string& path);

    // Generates HILTI code to initialize the matching state for finding the
    // next token.
    shared_ptr<hilti::Expression> _hiltiMatchTokenInit(const string& name, const std::list<shared_ptr<production::Literal>>& literals);

    // Performs the matching of the next token. Throws execeptions if the matching fails.
    shared_ptr<hilti::Expression> _hiltiMatchTokenAdvance(shared_ptr<hilti::Expression> mstate);

    // Adds the standard error cases for a switch statement switching on the match result.
    shared_ptr<hilti::builder::BlockBuilder> _hiltiAddMatchTokenErrorCases(shared_ptr<Production> prod,
                                                                           hilti::builder::BlockBuilder::case_list* cases,
                                                                           shared_ptr<hilti::builder::BlockBuilder> repeat,
                                                                           std::list<shared_ptr<production::Literal>> expected
                                                                          );

    // Raises a ParseError exception.
    void _hiltiParseError(const string& msg);

    // Gnerates the HILTI code to handle an out-of-input situation by
    // retrying next time if possible.
    void _hiltiYieldAndTryAgain(shared_ptr<Production> prod, shared_ptr<hilti::builder::BlockBuilder> builder, shared_ptr<hilti::builder::BlockBuilder> cont);

    // Generates the HILTI code to report insufficient input during matching.
    shared_ptr<hilti::Expression> _hiltiInsufficientInputHandler(bool eod_ok = false, shared_ptr<hilti::Expression> iter = nullptr);

    // Returns a BinPAC expression of type BinPAC::ByteOrder that specifies
    // the byte-order for unpacking the field. If the field has a &byteorder
    // attribute, that's used; if not the unit-wide default is taken. If none
    // is defined, returns null; the caller should then use network order as
    // default.
    shared_ptr<binpac::Expression> _fieldByteOrder(shared_ptr<type::unit::item::Field> field, shared_ptr<type::Unit> unit);

    // Returns a HILTI expression of type Hilti::Packed specifying the unpack
    // format for an integer of the given width/signedness/byteorder
    // combiniation. The byteorder must be a BinPAC expression of type
    // BinPAC::ByteOrder (as, e.g., returned by _fieldByteOrder(). If \a
    // byteorder is null, network order is used as default.
    shared_ptr<hilti::Expression> _hiltiIntUnpackFormat(int width, bool signed_, shared_ptr<binpac::Expression> byteorder);

    // Disables saving parsed values in a parse objects. This is primarily
    // for parsing container items that aren't directly stored there.
    void disableStoringValues();

    // Renables saving parsed values in a parse objects. This is primarily
    // for parsing container items that aren't directly stored there.
    void enableStoringValues();

    // Returns true if storing values in the parse object is enabled.
    bool storingValues();

    std::list<shared_ptr<ParserState>> _states;
    shared_ptr<hilti::Expression> _last_parsed_value;
    int _store_values;
};

}
}

#endif
