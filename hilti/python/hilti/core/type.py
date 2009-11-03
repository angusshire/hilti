# $Id$

builtin_type = type

import types 
import inspect

import util

### Base classes

class Type(object):
    """Base class for all data types provided by the HILTI language.  
    
    name: string - The name of type in a readable form suited to present to
    the user (e.g., in error messages and debugging output).
        
    docname: streing - Optional string which, if given, will be used in the
    automatically generated instruction documentation instead of *name*; it is
    not used anywhere else than in the documentation.

    Note:
    
    Throughout the HILTI compiler, type compatibility is checked by applying
    Python's ``==`` operator to Type-derived objects. A comparision of the
    form ``t == other``, with *t* being an instance of Type or any derived
    class, is performed according to these rules:
    
    * If *other* is likewise an instance of Type, the two types match
      according to the following conditions:
    
      1. If the two types are instances of the same class (exact match; *not*
         considering any common ancestors), the match succeeds if the
         type-specific :meth:`cmpWithSameType` method returns True. The
         default implementation of this method as defined in Type compares the
         results of two objects :class:`name` methods. 
         
      2. If either of the two types is an instance of ~~Any, the match succeeds.

      3. If neither (1) or (2) is the case, the match fails. 
      
    * If *other* is a *class* that is derived from Type, then the match
      succeeds if and only if *t* is an instance of any class derived from
      *other*. 
      
    * If *other* is a tuple or list, then *t* is recursively compared to any
      elements contained therein, and the match succeeds if at least one
      element matches with *t*. 

    * In all other cases, the comparision yields False.
      
    Any class derived from Type must include a class-variable ``_name``
    containing a string that is suitable for use in error messages to
    describes the HILTI type that the class is representing. In addition, all
    Type-derived classes that can be instantiated directly (vs. base classes)
    must have another class-variable *_id* with an integer that is unique
    across all of them; the integer must have a matching constant 
    ``__HLT_TYPE_*`` defined in :download:`/libhilti/hilti_intern.h`. 
    
    Todo: Perhaps we should autogenerate the *_id* constants in some way and
    also automatically synchronize them with ``hilti_intern.h``. I'm however
    not quite sure what's an elegant way to do that. 
    """
    def __init__(self, name, docname=None):
        self._name = name
        self._docname = docname if docname else name
    
    def name(self):
        """Returns the name of the type.
        
        Returns: string - The name of the type.
        """
        return self._name
    
    def docname(self):
        """Returns the name of the type as used in the instruction
        documentation.
        
        Returns: string - The documentation name of the type.
        """
        return self._docname

    def cmpWithSameType(self, other):
        """Compares with another objects of the same class. The default
        implementation compares the results of the two instances'
        :meth:`name`` methods. Derived classes can override the method 
        to implement their own type checking.
        
        Returns: bool - True if the two objects are compatible. 
        """
        assert self.__class__ == other.__class__
        return self.name() == other.name()
    
    def __str__(self):
        return self.name()
    
    def __eq__(self, other):
        # Special case for tuples/list: one of the members has to match.
        if builtin_type(other) == types.ListType or builtin_type(other) == types.TupleType:
            for t in other:
                if self == t:
                    return True
                
            return False

        # Special case for classes: if we're an instance of that class, we're
        # fine.
        if inspect.isclass(other):
            return _matchWithTypeClass(self, other)
        
        # We match any Any instance.
        if isinstance(other, Any):
            return True
        
        # If we are Any, we match everything else.
        if isinstance(self, Any) and isinstance(other, Type):
            return True

        # If we're the same kind of thing, ask the derived class whether we
        # match; except for the wildcard types which we handle directly.
        if builtin_type(self) == builtin_type(other):
            if self.wildcardType() or other.wildcardType():
                return True
            
            return self.cmpWithSameType(other)
        
        # Comparision with any other type has failed now.
        if isinstance(other, Type):
            return False
            
        # Can't tell.
        return NotImplemented

    def __ne__(self, other):
        eq = self.__eq__(other)
        return not eq if eq != NotImplemented else NotImplemented
    
    _name = "type"
    _id = 0 # Zero is used as an error indicator.

class MetaType(Type):
    """Type representing a type."""
    def __init__(self):
        super(MetaType, self).__init__("meta type")

    _name = "meta type"

import sys    
    
Wildcard = "<wildcard>"    
"""Global used by the parser for a type parameter to indicate a wildcard."""

class HiltiType(Type):
    """Base class for all HILTI types that can be directly instantiated in a
    HILTI program. That includes use in global and local variables, as well as
    allocation on the heap. 
    
    During run-time, libhilti will provide a type-info objects for all
    HiltiType instances.
    
    args: list of any - Type parameters, or the empty list for
    non-parameterized types.  If a derived class detects an error with any of
    the arguments, it must raise a ~~ParameterMismatch exception.
    
    wildcard: bool - True if the type allows a wildcard type to be specified
    as ``name<*>``. Such a wildcard type will always match all other instances
    of the same type.
    
    name: string - Same as for :meth:`~hilti.core.type.type`. 
    docname: string - Same as for :meth:`~hilti.core.type.type`.
    itertype: ~~Iterator-derived *class* - If type is iterable, the type of the iterator;
    otherwise None. 
    
    Raises: ~~ParameterMismatch - Raised when there's a problem with one of
    the type parameters. The error should not have been reported to the user
    already; an error message will be constructed from the exeception's
    information.
    
    Note: For HiltiTypes, it is important that the results of their ~~name
    methods can be used to identify the types, including any potential
    parameters. In particular, if two HiltiTypes share the same name, they are
    considered equivalent, and likewise HiltiTypes with different names are
    considered non-equivalent. This is achieved automatically though by
    appending a readable representation of all parameters to the type's base
    name passed to the ctor via *name*.
    """
    def __init__(self, args, name, wildcard=False, itertype=None, docname=None):
        super(HiltiType, self).__init__(name, docname=docname)

        if not isinstance(args, list) and not isinstance(args, tuple):
            args = [args]
            
        self._itertype = itertype

        if len(args) == 1 and args[0] is Wildcard:
            
            if not wildcard:
                raise HiltiType.ParameterMismatch(self._type, "type does not accept wildcards")
            
            self._name = "%s<*>" % name
            self._args = []
            self._wildcard = True
            return
        
        if args:
            self._name = "%s<%s>" % (name, ",".join([str(arg) for arg in args]))
            
            for a in args:
                if a is Wildcard:
                    raise HiltiType.ParameterMismatch(self, "type arguments cannot be a wildcard here")
        
        self._wildcard = False
        self._args = args
        self._itertype = itertype

    _name = "HILTI type"

    def args(self):
        """Returns the type's parameters.
        
        args: list of any - The type parameters, or the empty list for
        non-parameterized types and wildcard types.  
        """
        return self._args

    def wildcardType(self):
        """Returns whether this type matches any instanced of the same type.
        
        Returns: bool - True if a wildcard type.
        """
        return self._wildcard
    
    def iteratorType(self):
        """Returns the type of iterators. Returns None if the type is not
        iterable.
        
        Returns: ~~Iterator - The iterator type or None if not iterable. 
        """
        return self._itertype

    class ParameterMismatch(Exception):
        """Exception class to indicate a problem with a type parameter.
        
        param: any - The parameter which caused the trouble.
        reason: string - A string explaining what went wrong.
        """
        def __init__(self, param, reason):
            self._param = param
            self._reason = reason
            
        def __str__(self):
            return "error in type parameter: %s (%s)" % (self._reason, self._param)

        
class ValueType(HiltiType):
    """Base class for all types that can be directly stored in a HILTI
    variable. Types derived from ValueType cannot be allocated on the heap.
    
    The arguments are the same as for ~~HiltiType.
    """
    def __init__(self, args, name, **kwargs):
        super(ValueType, self).__init__(args, name, **kwargs)

    _name = "storage type"
        
class HeapType(HiltiType):
    """Base class for all types that must be allocated on the heap. Types
    derived from HeapType cannot be stored directly in variables and only
    accessed via a ~~Reference. 
    
    The arguments are the same as for ~~HiltiType.
    """
    def __init__(self, args, name, **kwargs):
        super(HeapType, self).__init__(args, name, **kwargs)

    _name = "heap type"

class Container(HeapType):
    """Base class for all container types. A container is iterable and stores
    elements of a certain *item type*. 
    
    The arguments are the same as for ~~HiltiType. If it's not a wildcard
    type, the first argument must be the item type, a ~~ValueType. 
    """
    def __init__(self, args, name, **kwargs):
        super(HeapType, self).__init__(args, name, **kwargs)
        
        if self.wildcardType():
            self._type = None
            return

        assert len(args) >= 1
        t = args[0]
        
        if not isinstance(t, ValueType):
            raise HiltiType.ParameterMismatch(t, "container type must be a value type")
        
        self._type = t
        
    def itemType(self):
        """Returns the type of the container items.
        
        Returns: ~~ValueType - The type of the channel items.
        """
        return self._type
        
    _name = "container type"
    
class OperandType(Type):
    """Base class for all types that can only be used as operands and function
    arguments. These types cannot be stored in variables nor on the heap. 
    
    The arguments are the same as for ~~Type.
    """
    def __init__(self, name, **kwargs):
        super(OperandType, self).__init__(name, **kwargs)
        
    _name = "operand type"
    
class TypeDeclType(Type):
    """Base class for types that represent an otherwise declared HILTI type.
    
    t: ~~Type - The declared type.
    docname: string - Same as for :meth:`~hilti.core.type.type`.
    """
    def __init__(self, t, docname=None):
        super(TypeDeclType, self).__init__(t.name(), docname)
        self._type = t

    def type(self):
        """Returns the declared type..
        
        Returns: ~~Type - The declared type.
        """
        return self._type
        
    def declType(self):
        """Returns the declared type. This is an alias for ~~type.
        
        Returns: ~~Type - The declared type.
        """
        return self._type

    _name = "type-declaration type"

class Iterator(ValueType):
    """Type for iterating over a container. 
    
    t: ~~HeapType - The container type to iterate over. 
    """
    def __init__(self, t):
        super(Iterator, self).__init__([t], Iterator._name)

        self._elem_type = t
        if not isinstance(t, HiltiType):
            raise HiltiType.ParameterMismatch(self._type, "iterator takes a type as parameter")

    def containerType(self):
        """Returns the container type.
        
        Returns: ~~HeapType - The container type the iterator can iterator over.
        """
        return self._elem_type
        
    _name = "iterator"
    
# Actual types.    

class String(ValueType):
    """Type for strings."""
    def __init__(self):
        super(String, self).__init__([], String._name)
        
    _name = "string"
    _id = 3
        
class Integer(ValueType):
    """Type for integers.  
    
    args: int, or a list containing a single int. - The integer specifies the
    bit-width of integers represented by this type."""
    def __init__(self, args):
        super(Integer, self).__init__(args, Integer._name, wildcard=True)

        if self.wildcardType():
            self._width = 0
            return 
        
        if type(args) == types.IntType or type(args) == types.StringType:
            args = [args]

        assert len(args) == 1
        
        try:
            self._width = int(args[0])
        except ValueError:
            raise HiltiType.ParameterMismatch(args[0], "cannot convert to integer")
        
        if self._width < 0 or self._width > 64:
            raise HiltiType.ParameterMismatch(args[0], "integer width must be between 1 and 64 bits")

    def width(self):
        """Returns the bit-width of the type's integers.
        
        Returns: int - The number of bits available to represent integers of
        this type. If the returned width is zero, the type matches all other
        integer types. 
        """
        return self._width

    def setWidth(self, width):
        """Sets the bit-width of the type's integers.
        
        width: int - The new bit-width. 
        """
        self._width = width
    
    def cmpWithSameType(self, other):
        if self._width == 0 or other._width == 0:
            return True
        
        return self._width == other._width
    
    _name = "int"
    _id = 1

class Enum(ValueType):
    """Type for enumerations. Each label of the enumerations is mapped to a
    unique integer. In addition to the user-defined labels, there is always an
    implicitly defined value ``Undef``. 
    
    labels: list of string - The labels that make up the possible values of
    the enumeration. 
    """
    def __init__(self, labels):
        name = "enum { %s }" % ", ".join(labels)
        super(Enum, self).__init__([], name)
        
        i = 0
        self._labels = {}
        for t in ["Undef"] + labels:
            self._labels[t] = i
            i += 1
            
    def labels(self):
        """Returns the enums labels with their corresponding integer values.
        
        Returns: dictonary string -> int - The labels mappend to their values.
        """
        return self._labels

    _name = "enum"
    _id = 10
    
class Bitset(ValueType):
    """Type for bitsets. Each bit label is mapped to a unique integer
    corresponding to its bit number.
    
    labels: list of (string, bit) - The labels and bit numbers that make up
    the possible values of the bitset. 
    """
    def __init__(self, labels):
        self._labels = {}
        next = 0
        for (label, bit) in labels:
            if bit == None:
                bit = next 
                
            if bit >= 64:
                raise HiltiType.ParameterMismatch(self, "bitset can only store bits 0..63")
            
            next = max(next, bit + 1)
            self._labels[label] = bit
        
        bits = ["%s = %s" % (label, str(bit)) for (label, bit) in self._labels.items()]
        name = "bitset { %s }" % ", ".join(bits)
        super(Bitset, self).__init__([], name)

    def labels(self):
        """Returns the bit labels with their corresponding bit numbers.
        
        Returns: dictonary string -> int - The labels mappend to their values.
        """
        return self._labels

    _name = "bitset"
    _id = 19
    
class Double(ValueType):
    """Type for doubles."""
    def __init__(self):
        super(Double, self).__init__([], Double._name)
        
    _name = "double"
    _id = 2

class Bool(ValueType):
    """Type for booleans."""
    def __init__(self):
        super(Bool, self).__init__([], Bool._name)
        
    _name = "bool"
    _id = 3

class Tuple(ValueType):
    """A type for tuples of values. 
    
    types: list of ~~Type - The types of the individual tuple elements."""
    def __init__(self, args):
        super(Tuple, self).__init__(args, Tuple._name, wildcard=True)

        if self.wildcardType():
            self._types = []
            self._any = True
            return
        
        assert types
        
        self._types = args
        self._any = False
            
    def types(self):
        """Returns the types of the typle elements.
        
        Returns: list of ~~ValueType - The types.
        """
        return self._types
        
    def cmpWithSameType(self, other):
        return self.types() == other.types()
        
    _name = "tuple"
    _id = 5

class Reference(ValueType):
    """Type for reference to heap objects.  

    args: list of single ~~HeapType - The type of the object referenced.
    """
    def __init__(self, args):
        super(Reference, self).__init__(args, Reference._name, wildcard=True)
        
        if self.wildcardType():
            self._type = Integer(8) # We use this as dummy type for the Null reference.
            return

        assert len(args) == 1
        
        if not isinstance(args[0], HeapType):
            raise HiltiType.ParameterMismatch(t, "reference type must be a heap type")
        
        self._type = args[0]

    def refType(self):
        """Returns the type referenced.
        
        Returns: ~~HeapType - The type referenced if any, or None if it's a
        wildcard type.
        """
        return self._type
        
    def cmpWithSameType(self, other):
        return self._type == other._type
    
    _name = "ref"
    _id = 6

class Addr(ValueType):
    """Type for IP addresses."""
    def __init__(self):
        super(Addr, self).__init__([], Addr._name)
        
    _name = "addr"
    _id = 12

class Net(ValueType):
    """Type for network prefixes."""
    def __init__(self):
        super(Net, self).__init__([], Net._name)
        
    _name = "net"
    _id = 17
    
class Port(ValueType):
    """Type for TCP and UDP ports."""
    def __init__(self):
        super(Port, self).__init__([], Port._name)
        
    _name = "port"
    _id = 13

class Overlay(ValueType):
    """Type for Overlays."""
    
    class Field:
        def __init__(self, name, start, type, fmt, arg = None):
            """
            Defines one field of the overlay.
            
            name: string - The name of the field.
            
            start: integer or string - If an integer, the field is assumed to
            be the offset in bytes from the start of the overlay where the
            field's data starts. If it's a string, the string must be the name
            of an another field and the added field is then assumed to start
            right after that one. 
            
            type: ~~Type - The type of the field. 
            
            fmt: integer or ~~ID - If an integer, the value must correspond to
            the internal enum value of ``Hilti::Packed`` label defining the
            format used for unpacked the field. If an ID, then the ID's name
            must be ``Hilti::Packed`` label. The ~~Resolver will turn such IDs
            into the corresponding integer. 
            
            Note: Instances of this class will have attributes named after the
            ctor's arguments, which can be directly accessed.
            """
            self.name = name
            self.start = start
            self.type = type
            self.fmt = fmt
            self.arg = arg
            
            self._deps = []
            self._offset = -1
            self._idx = -1
            
        def offset(self):
            """Returns the constant offset for the field. 
        
            Returns: integer - The offset in bytes from the start of the overlay.
            If the name defines a field with a non-constant offset, -1 returned.
            """
            return self._offset
        
        def dependants(self):
            """Returns all other fields the field depends on for its
            starting position.
    
            Returns: list of string - The names of other fields which are
            required to calculate the starting offset for this field. The
            list will be sorted in the order the fields were added to the
            overlay by ~~addField. If the named field starts at a constant
            offset and does not depend on any other fields, an empty list
            is returned.
            """
            return self._deps
        
        def depIndex(self):
            """Returns an index unique across all fields that are directly
            determining the starting position of another field with a
            non-constant offset.  All of these fields are sequentially
            numbered, starting with one.
            
            Returns: integer - The index of this field, or -1 if the field
            does not determine another's offset directly. 
            """
            return self._idx
        
    def __init__(self):
        super(Overlay, self).__init__([], Overlay._name)
        
        self._fields = {}
        self._deps = {}
        self._idxcnt = 0
        
    def addField(self, field):
        """Adds a field to an overlay. If the *field*'s *start* attribute
        specifies another field's name, that one must already have been added
        earlier.
        
        field: ~~Field - The field to be added.         
        """

        if field.name in self._fields:
            raise HiltiType.ParameterMismatch(args[0], "field %s already defined" % field.name)
        
        if isinstance(field.start, str):
            # Field depends on another one. 
            if not field.start in self._fields:
                raise HiltiType.ParameterMismatch(args[0], "field %s not yet defined" % field.start)

            field._deps = self._fields[field.start]._deps + [field.start]
            
            start = self._fields[field.start]
            if start._idx == -1:
                self._idxcnt += 1
                start._idx = self._idxcnt
            
        else:
            # Field has a constant offset.
            field._offset = field.start
        
        self._fields[field.name] = field 

    def fields(self):
        """Returns a list of all defined fields.
        
        Returns: list of ~~Field - The fields.
        """
        return self._fields.values()
        
    def field(self, name):
        """Returns the named field.
        
        name: string - Name of the field requested.
        
        Returns: ~~Field - The field, or None if there's no such field.
        """
        return self._fields.get(name, None)

    def numDependencies(self):
        """Returns the number of fields that other fields directly depend on
        for their starting position. This number is guaranteed to be not
        higher than the largest ~depIndex in this overlay.
        
        Returns: integer - The number of fields. 
        """
        return self._idxcnt
        
    _name = "overlay"
    _id = 14
    
class Struct(HeapType):
    """Type for structs. 
    
    fields: list of (~~ID, ~~Operand) - The fields of the struct, given as
    tuples of an ID and an optional default value; if a field does not have a
    default value, use None as the operand.
    """
    def __init__(self, fields):
        name = "struct { %s }" % ", ".join(["%s %s" % (id.name(), id.type().name()) for (id, op) in fields])
        super(Struct, self).__init__([], name)
        self._ids = fields
    
    def Fields(self):
        """Returns the struct's fields.
        
        Returns: list of (~~ID, ~~Operand) - The struct's fields, given as
        tuples of an ID and an optional default value.
        """
        return self._ids

    _name = "struct"
    _id = 7

class Bytes(HeapType):
    """Type for ``bytes``. 
    """
    def __init__(self):
        super(Bytes, self).__init__([], Bytes._name, itertype=IteratorBytes(self))

    _name = "bytes"
    _id = 9
    
class IteratorBytes(Iterator):
    """Type for iterating over ``bytes``. 
    """
    def __init__(self, t):
        super(IteratorBytes, self).__init__(t)

    _id = 100

class Channel(Container):
    """Type for channels. 

    args: list of ~~ValueType - The first argument is the type of the channel
    items. The second argument represents the channel capacity, i.e., the
    maximum number of items per channel. If the capacity equals to 0, it is
    assumed that the channel is unbounded.
    """
    def __init__(self, args):
        super(Channel, self).__init__(args, Channel._name, wildcard=True)

        if self.wildcardType():
            self._capacity = 0
            return

        assert len(args) == 2
        t = args[0]        
        
        if args[1] == "_":
            self._capacity = 0 
        else:
            try:
                self._capacity = int(args[1])
            except ValueError:
                raise HiltiType.ParameterMismatch(args[1], "cannot convert to integer")
            
            if self._capacity < 0:
                raise HiltiType.ParameterMismatch(args[1], "channel capacity cannot be negative")
            
    def capacity(self):
        """Returns channel capacity, i.e., the maximum number of items that the
        channel can hold.
        
        Returns: ~~ValueType - The channel capacity. A capacity of 0 denotes an
        unbounded channel.
        """
        return self._capacity

    _name = "channel"
    _id = 8

class Vector(Container):
    """Type for ``vector``. 
    
    args: list of ~~ValueType - The list must have exactly one element: the
    type of the vector's elements. 
    
    """
    def __init__(self, args):
        super(Vector, self).__init__(args, Vector._name, wildcard=True, itertype=IteratorVector(self))

        if not self.wildcardType():
            assert len(args) == 1
        
    _name = "vector"
    _id = 15
    
class IteratorVector(Iterator):
    """Type for iterating over ``vector``. 
    """
    def __init__(self, t):
        super(IteratorVector, self).__init__(t)
        
    _id = 101
    
class List(Container):
    """Type for ``list``. 
    
    args: list of ~~ValueType - The list must have exactly one element: the
    type of the list's elements. 
    
    """
    def __init__(self, args):
        super(List, self).__init__(args, List._name, wildcard=True, itertype=IteratorList(self))
        
        if not self.wildcardType():
            assert len(args) == 1

    _name = "list"
    _id = 15
    
class IteratorList(Iterator):
    """Type for iterating over ``list``. 
    """
    def __init__(self, t):
        super(IteratorList, self).__init__(t)
        
    _id = 102

class RegExp(HeapType):
    """Type for ``regexp``. 
    """
    def __init__(self):
        super(RegExp, self).__init__([], RegExp._name)

    _name = "regexp"
    _id = 18
    
class Function(Type):
    """Type for functions. 
    
    args: list of (~~ID, default) tuples - The function's arguments, with
    *default* being optional default values. Set *default* to *None* if no
    default.
    
    resultt - ~~Type - The type of the function's return value (~~Void for none). 
    """
    def __init__(self, args, resultt):
        name = "function (%s) -> %s" % (", ".join([str(id.type()) for (id, default) in args]), resultt)
        super(Function, self).__init__(name)
        self._ids = [id for (id, default) in args]
        self._defaults = [default for (id, default) in args]
        self._result = resultt
        
    def args(self):
        """Returns the functions's arguments.
        
        Returns: list of ~~ID - The function's arguments. 
        """
        return self._ids

    def argsWithDefaults(self):
        """Returns the functions's arguments with any default values.
        
        Returns: list of (~~ID, default) - The function's arguments with their
        default values. If there's no default for an arguments, *default*
        will be None.
        """
        return zip(self._ids, self._defaults)
    
    def getArg(self, name):
        """Returns the named function argument.
        
        Returns: ~~ID - The function's argument with the given name, or None
        if there is no such arguments. 
        """
        for id in self._ids:
            if id.name() == name:
                return id
            
        return None
    
    def resultType(self):
        """Returns the functions's result type.
        
        Returns: ~~Type - The function's result. 
        """
        return self._result

    _name = "function"

class Label(OperandType):
    """Type for block labels."""
    def __init__(self):
        super(Label, self).__init__("label")

    _name = "label"
    
class Void(OperandType):
    """Type representing a non-existing function result."""
    def __init__(self):
        super(Void, self).__init__("void")
        
    _name = "void"
    
class Any(OperandType):
    """Wildcard type that matches any other type."""
    def __init__(self):
        super(Any, self).__init__("any")

    _name = "any"

class Unknown(OperandType):
    """Place-holder type when the real type is unknown. This type is used
    during parsing when the final types have not been determined yet."""
    def __init__(self):
        super(Unknown, self).__init__("unknown")

    _name = "unknown"

class Exception(HeapType):
    """Type for ``exception``. 
    
    ename: string - The name of the exception type. 
    
    argtype: type.ValueType - The type of the optional exception argument, or None if no
    argument. If *baseclass* is specified and *baseclass* has an argument,
    *argtype* must match that one. 
    
    baseclass: type.Exception - The base exception class this one is derived
    from, or None if it should be derived from the built-in top-level
    ``Hilti::Exception`` class. 
    """
    def __init__(self, ename, argtype, baseclass):
        name = "exception %s (%s) : %s" % (ename, argtype, str(baseclass) if baseclass else "Hilti::Exception")
        super(Exception, self).__init__([], Exception._name)
        self._ename = ename
        self._argtype = argtype
        self._baseclass = baseclass

    def exceptionName(self):
        """Return the name of the exception type."""
        return self._ename
        
    def argType(self):
        """Returns the type of the exception's argument.
        
        Returns: Type - The type, or None if no argument.
        """
        return self._argtype
    
    def baseClass(self):
        """Returns the type of the exception's base class.
        
        Returns: type.Exception - The type of the base class.
        """
        return self._baseclass if self._baseclass else Exception._root
    
    def setBaseClass(self, base):
        """Set's the type of the exception's base class.
        
        base: type.Exception - The type of the base class.
        """
        self._baseclass = base
    
    def isRootType(self):
        """Checks whether the exception type represents the top-level root type.
        
        Returns: bool - True if *t* is the root exception type. 
        """
        return id(self) == id(Exception._root)
        
    _name = "exception"
    _id = 20

# Special place-holder for the root of all exceptions. 
Exception._root = Exception("$Root$", None, None)
    
class Continuation(HeapType):
    """Type for ``continuation``.
    
    Note: Currently, this is an internal type that cannot directly be created
    by an HILTI program.
    """
    def __init__(self):
        super(Continuation, self).__init__([], Continuation._name)

    _name = "continuation"
    _id = 21
    
def _matchWithTypeClass(t, cls):
    """Checks whether a type instance matches with a type class; cls can be a tuple
    of classes as well."""

    # Special case for tuples/lists of classes, for which a match with any
    # of the classes in there is fine. 
    if builtin_type(cls) == types.ListType or builtin_type(cls) == types.TupleType:
        for cl in cls:
            if cl and _matchWithTypeClass(t, cl):
                return True
            
        return False
        
    # Special case for the Any class, which matches any other type.
    if cls == Any:
        return True

    # Standard case, need match with the cls's type hierarchy.
    return isinstance(t, cls)

def fmtTypeClass(cls, doc=False):
    """Returns a readable representation of a type class.
    
    cls: class derived from ~~Type, or a list/tuple of such classes - The type
    to be converted into a string; if a list or tuple is given, all elements
    are converted individually and merged in tuple-syntax.
    
    doc: boolean - If true, the string is formatted for inclusion into the
    automatically generated documentation; the format then will be slightly
    different.
    
    Returns: string - The readable representation.
    """
    if cls == None:
        return "none"
    
    if builtin_type(cls) == types.ListType or builtin_type(cls) == types.TupleType:
        if not doc:
            return " or ".join([fmtTypeClass(t) for t in cls])
        else:
            return "|".join([fmtTypeClass(t) for t in cls])

    return cls._name
    
# List of keywords that the parser will understand to instantiate types.  Each
# keyword is mapped to a tuple (class, args, defaults) where "class" is the
# name of the class to instantiate for this keyword; num_args is the number
# of type parameters this type expects (-1 for variable but one minimum); and
# default is an optional list with predefined parameters to be used *instead* of
# user-supplied params (optional). All classes given here must be derived from
# HiltiType.

_keywords = {
	"int": (Integer, 1, None),
	"int8": (Integer, 1, [8]),
	"int16": (Integer, 1, [16]),
	"int32": (Integer, 1, [32]),
	"int64": (Integer, 1, [64]),
	"double": (Double, 0, None),
    "string": (String, 0, None),
    "bool": (Bool, 0, None),
    "tuple": (Tuple, -1, None),
    "ref": (Reference, 1, None),
    "channel": (Channel, 2, None),
    "bytes": (Bytes, 0, None),
    "iterator": (Iterator, 1, None),
    "addr": (Addr, 0, None),
    "net": (Net, 0, None),
    "port": (Port, 0, None),
    "vector": (Vector, 1, None),
    "list": (List, 1, None),
    "regexp": (RegExp, 0, None),
    }

_all_hilti_types = {}
    
def getHiltiType(name, args = []):
    """Instantiates a ~~HiltiType from a type name. 
    
    *name*: string - The name of type as used in HILTI programs. 
    *args*: list of any - A list of type parameters if the type is
    parametrized; the empty list for non-parameterized types.
    
    Returns: tuple (success, result) - If *success* is True, the type was
    successfully instantiated and *result* will be the newly created type
    object. If *success* is False, there was an error and *result* will be a
    string containing an error message."""
    try:
        (cls, num_args, defs) = _keywords[name]
    except KeyError:
        return (False, "no such type, %s" % name)
    
    if args and (num_args == 0 or defs != None):
        return (False, "type %s does not accept type paramters" % name)
    
    wrong_args = False
    
    if args and num_args >= 0 and len(args) != num_args and not (args == Wildcard or args == [Wildcard]):
        wrong_args = True
    
    if num_args == -1 and not args:
        wrong_args = True
        
    if  not args and not defs and num_args > 0:
        wrong_args = True

    if wrong_args:
        return (False, "wrong number of parameters for type %s (expected %d, have %d)" % (name, num_args, len(args)))
    
    if defs:
        args = defs
        
    # Special-case iterators here: we need to create instances of the right
    # sub-class here. 
    if cls == Iterator:
        container = args[0]
        
        if not isinstance(container, HiltiType):
            return (False, "%s is not a type" % container)
        
        if not container.iteratorType():
            return (False, "%s is not iterable" % container)
        
        return (True, container.iteratorType())
        
    try:
        if args:
            t = cls(args)
        else:
            t = cls()
            
        try:
            return (True, _all_hilti_types[t.name()])
        except KeyError:
            if not t.wildcardType():
                _all_hilti_types[t.name()] = t
            return (True, t)
        
    except HiltiType.ParameterMismatch, e:
        return (False, str(e))

def registerHiltiType(t):
    """Registers an already instantiated ~~HiltiType with the compiler. This
    must be called once for all user-defined types such as structs."""
    _all_hilti_types[t.name()] = t
    
def getHiltiTypeNames():
    """Returns a list of HILTI types. The list contains the names of all types
    that correspond to a ~~HiltiType-derived class. The names can be used with
    :meth:`getHiltiType` to instantiate a corresponding type object.
    
    Returns: list of strings - The names of the types.
    """
    return _keywords.keys()
    
def getAllHiltiTypes():
    """Returns a list of all HILTI types. The list contains all instances of
    ~~HiltiType that have been created so far.
    
    Returns: list ~~HiltiType - The complete set of HILTI types.
    """
    return _all_hilti_types.values()
