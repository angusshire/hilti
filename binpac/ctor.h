
#ifndef BINPAC_CTOR_H
#define BINPAC_CTOR_H

#include <stdint.h>

#include <ast/ctor.h>
#include <ast/visitor.h>

#include "common.h"
#include "passes/printer.h"

namespace binpac {

/// Base class for ctor nodes. A ctor instantiates a HeapType.
class Ctor : public ast::Ctor<AstInfo>
{
public:
    /// Constructor.
    ///
    /// l: An associated location.
    Ctor(const Location& l=Location::None);

    /// Returns a readable representation of the ctor.
    string render() override;

    ACCEPT_VISITOR_ROOT();
};

namespace ctor {

/// AST node for a bytes constructor.
class Bytes : public Ctor
{
public:
    /// Constructor.
    ///
    /// b: The value to initialize the bytes object with.
    ///
    /// l: An associated location.
    Bytes(const string& b, const Location& l=Location::None);

    /// Returns the initialization value.
    const string& value() const;

    /// Returns the type of the constructed object.
    shared_ptr<Type> type() const override;

    ACCEPT_VISITOR(Ctor);

private:
    string _value;
};

/// AST node for a list constructor.
class List : public Ctor
{
public:
    /// Constructor.
    ///
    /// etype: The type of the the list's elements. Can be left null type can
    /// be derived form \a elems.
    ///
    /// elems: The elements for the instance being constructed.
    ///
    /// l: An associated location.
    List(shared_ptr<Type> etype, const expression_list& elems, const Location& l=Location::None);

    /// Returns the initialization value.
    expression_list elements() const;

    /// Returns the type of the constructed object. If the container has
    /// elements, the type will infered from those. If not, it will be a
    /// wildcard type.
    shared_ptr<Type> type() const;

    ACCEPT_VISITOR(Ctor);

private:
    node_ptr<Type> _type;
    std::list<node_ptr<Expression>> _elems;
};

/// AST node for a vector constructor.
class Vector : public Ctor
{
public:
    /// Constructor.
    ///
    /// etype: The type of the the vector's elements. Can be left null type
    /// can be derived form \a elems.
    ///
    /// elems: The elements for the instance being constructed.
    ///
    /// l: An associated location.
    Vector(shared_ptr<Type> etype, const expression_list& elems, const Location& l=Location::None);

    /// Returns the initialization value.
    expression_list elements() const;

    /// Returns the type of the constructed object. If the container has
    /// elements, the type will infered from those. If not, it will be a
    /// wildcard type.
    shared_ptr<Type> type() const;

    ACCEPT_VISITOR(Ctor);

private:
    node_ptr<Type> _type;
    std::list<node_ptr<Expression>> _elems;
};

/// AST node for a set constructor.
class Set : public Ctor
{
public:
    /// Constructor.
    ///
    /// etype: The type of the the set's elements. Can be left null type can
    /// be derived form \a elems.
    ///
    /// elems: The elements for the instance being constructed.
    ///
    /// l: An associated location.
    Set(shared_ptr<Type> etype, const expression_list& elems, const Location& l=Location::None);

    /// Returns the initialization value.
    expression_list elements() const;

    /// Returns the type of the constructed object. If the container has
    /// elements, the type will infered from those. If not, it will be a
    /// wildcard type.
    shared_ptr<Type> type() const;

    ACCEPT_VISITOR(Ctor);

private:
    node_ptr<Type> _type;
    std::list<node_ptr<Expression>> _elems;
};

/// AST node for a list constructor.
class Map : public Ctor
{
public:
    typedef std::pair<node_ptr<Expression>,node_ptr<Expression>> element;
    typedef std::list<element> element_list;

    /// Constructor.
    ///
    /// ktype: The type of the map's index values.
    ///
    /// vtype: The type of the map's values.
    ///
    /// elems: The elements for the instance being constructed.
    ///
    /// l: An associated location.
    Map(shared_ptr<Type> ktype, shared_ptr<Type> vtype, const element_list& elems, const Location& l=Location::None);

    /// Returns the initialization value.
    element_list elements() const;

    /// Returns the type of the constructed object. If the container has
    /// elements, the type will infered from those. If not, it will be a
    /// wildcard type.
    shared_ptr<Type> type() const;

    ACCEPT_VISITOR(Ctor);

private:
    node_ptr<Type> _type;
    std::list<std::pair<node_ptr<Expression>,node_ptr<Expression>>> _elems;
};

/// AST node for a regexp constructor.
class RegExp : public Ctor
{
public:
    /// A pattern is a tuple of two strings. The first element is the regexp
    /// itself, and the second a string with optional patterns flags.
    /// Currently, no flags are supported though.
    typedef std::pair<string, string> pattern;

    /// A list of patterns.
    typedef std::list<pattern> pattern_list;

    /// Constructor.
    ///
    /// regexp: The regexp.
    ///
    /// flags: The string with flags.
    ///
    /// attrs: Type attributes that will become part of the returned type::RegExp.
    ///
    /// l: An associated location.
    RegExp(const string& regexp, const string& flags, const attribute_list& attrs = attribute_list(), const Location& l=Location::None);

    /// Constructor.
    ///
    /// patterns: List of patterns.
    ///
    /// attrs: Type attributes that will become part of the returned type::RegExp.
    ///
    /// l: An associated location.
    RegExp(const pattern_list& patterns, const attribute_list& attrs = attribute_list(), const Location& l=Location::None);

    /// Returns the pattern.
    const pattern_list& patterns() const;

    /// Returns the type of the constructed object. Pattern constants are
    /// always of type \c regexp<>. To add further type attributes, they need
    /// to be coerced to a regexp type that has them.
    shared_ptr<Type> type() const;

    ACCEPT_VISITOR(Ctor);

private:
    node_ptr<Type> _type;
    pattern_list _patterns;
};


}

}

#endif