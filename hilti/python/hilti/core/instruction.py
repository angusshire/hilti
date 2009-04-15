# $Id$

builtin_type = type

import ast
import type
import util
import constant

class Instruction(ast.Node):
    """Base class for all instructions supported by the HILTI language.
    To create a new instruction do however *not* derive directly from
    Instruction but use the :meth:`instruction` decorator.
    
    op1: ~~Operand - The instruction's first operand, or None if unused.
    op2: ~~Operand - The instruction's second operand, or None if unused.
    op3: ~~Operand - The instruction's third operand, or None if unused.
    target: ~~IDOperand - The instruction's target, or None if unused.
    location: ~~Location - A location to be associated with the instruction. 
    """
    
    _signature = None
    
    def __init__(self, op1=None, op2=None, op3=None, target=None, location=None):
        assert not target or isinstance(target, IDOperand)
        
        super(Instruction, self).__init__(location)
        self._op1 = op1
        self._op2 = op2
        self._op3 = op3
        self._target = target
        self._location = location
        
        cb = self.signature().callback()
        if cb:
            cb(self)

    def signature(self):
        """Returns the instruction's signature.
        
        Returns: ~~Signature - The signature.
        """
        return self.__class__._signature
            
    def name(self):
        """Returns the instruction's name. The name is the mnemonic as used in
        a HILTI program.
        
        Returns: string - The name.
        """
        return self.signature().name()
        
    def op1(self):
        """Returns the instruction's first operand.
        
        Returns: ~~Operand - The operand, or None if unused.
        """
        return self._op1
    
    def op2(self):
        """Returns the instruction's second operand.
        
        Returns: ~~Operand - The operand, or None if unused.
        """
        return self._op2
    
    def op3(self):
        """Returns the instruction's third operand.
        
        Returns: ~~Operand - The operand, or None if unused.
        """
        return self._op3

    def target(self):
        """Returns the instruction's target.
        
        Returns: ~~IDOperand - The target, or None if unused.
        """
        return self._target

    def setOp1(self, op):
        """Sets the instruction's first operand.
        
        op: ~~Operand - The new operand to set.
        """
        self._op1 = op
        
    def setOp2(self, op):
        """Sets the instruction's second operand.
        
        op: ~~Operand - The new operand to set.
        """
        self._op2 = op
    
    def setOp3(self, op):
        """Sets the instruction's third operand.
        
        op: ~~Operand - The new operand to set.
        """
        self._op3 = op
        
    def setTarget(self, target):
        """Sets the instruction's target.
        
        op: ~~IDOperand - The new operand to set.
        """
        assert not target or isinstance(target, IDOperand)
        self._target = target
        
    def __str__(self):
        target = "(%s) = " % self._target if self._target else ""
        op1 = " (%s)" % self._op1 if self._op1 else ""
        op2 = " (%s)" % self._op2 if self._op2 else ""
        op3 = " (%s)" % self._op3 if self._op3 else ""
        return "%s%s%s%s%s" % (target, self.signature().name(), op1, op2, op3)

    # Visitor support.
    def visit(self, visitor):
        visitor.visitPre(self)

        if self._op1:
            self._op1.visit(visitor)
            
        if self._op2:
            self._op2.visit(visitor)
            
        if self._op3:
            self._op3.visit(visitor)

        if self._target:
            self._target.visit(visitor)

        visitor.visitPost(self)

class Operator(Instruction):
    """Class for instructions that are overloaded by type. While most
    HILTI instructions are clearly tied to a particular type, *operators* are
    generic instructions that can operator on different types.
    
    To create a new operator do *not* derive directly from Operator but use
    the :meth:`operator` decorator.
    
    op1: ~~Operand - The operator's first operand, or None if unused.
    op2: ~~Operand - The operator's second operand, or None if unused.
    op3: ~~Operand - The operator's third operand, or None if unused.
    target: ~~IDOperand - The operator's target, or None if unused.
    location: ~~Location - A location to be associated with the operator. 
    
    Todo: For now, operators are always overloaded based on the type of their
    first operand. We should probably make that more flexibel sometime.
    """
    def __init__(self, op1=None, op2=None, op3=None, target=None, location=None):
        super(Operator, self).__init__(op1, op2, op3, target, location)
       
    """Returns the type on which the operator should be overloaded.
    
    Returns: ~~HiltiType - The type."""
    def operatorType(self):
        t = self.op1().type()
        if isinstance(t, type.TypeDeclType):
            return t.type()
        else:
            return t 

class OverloadedOperator(Instruction):
    """Class for overloading an Operator on a type-specific basis. For each
    ~~Operator a type wants to provide an overloaded implementation, it must
    be define an OverloadedOperator. However, to do so do *not* derive
    directly from this class but use the :meth:`overload` decorator.

    operator: ~~Operator class - The operator to be overloaded. 
    op1: ~~Operand - The operator's first operand.
    op2: ~~Operand - The operator's second operand, or None if unused.
    op3: ~~Operand - The operator's third operand, or None if unused.
    target: ~~IDOperand - The operator's target, or None if unused.
    location: ~~Location - A location to be associated with the operator. 
    """
        
    def __init__(self, operator, op1, op2=None, op3=None, target=None, location=None):
        super(Operator, self).__init__(op1, op2, op3, target, location)
        self._operator = operator
        
    def operator():
        """Returns the operator which is overloaded.
        
        Returns: ~~Operator class - The overload operator.
        """
        return self._operator
    
class Operand(ast.Node):
    """Base class for operands and targets of HILTI instructions. 
    
    value: any - The operand's value; must match with the *type*.
    type: ~~Type - The operand's type.
    location: ~~Location - A location to be associated with the operand. 
    """
    def __init__(self, value, type, location):
        super(Operand, self).__init__(location)
        self._value = value
        self._type = type
        self._location = location

    def value(self):
        """Return's the operand's value. 
        
        Returns: object - The operand's value.
        """
        return self._value
    
    def type(self):
        """Return's the operand's type. 
        
        Returns: object - The operand's type.
        """
        return self._type

    def _setValue(self, value):
        self._value = value
        
    def _setType(self, type):
        self._type = type
    
    def __str__(self):
        return "%s" % self._value

class ConstOperand(Operand):
    """Represents a constant operand. For a ConstOperand, :meth:`value()`
    returns the same value as the corresponding constant's ~~Constant.value.
    
    constant: ~~Constant - The constant value.
    location: ~~Location - A location to be associated with the operand. 
    """
    def __init__(self, constant, location=None):
        super(ConstOperand, self).__init__(constant.value(), constant.type(), location)
        self._constant = constant

    def constant(self):
        """Returns the operand's constant.
        
        Returns: ~~Constant - The constant value."""
        return self._constant
    
    def setConstant(self, const):
        """Sets the operand's constant.
        
        const: ~~Constant - The new constant value.
        """
        self._constant = const
        self._setValue(const.value())
        self._setType(const.type())
        
class IDOperand(Operand):
    """Represents an ID operand. For an IDOperand, :meth:`value()`
    returns the name of the corresponding ~~ID.
    
    id: ~~ID - The operand's ID.
    location: ~~Location - A location to be associated with the operand. 
    """
    def __init__(self, id, location=None):
        super(IDOperand, self).__init__(id, id.type(), location)
        self._id = id

    def id(self):
        """Returns the operand's ID.
        
        Returns: ~~ID - The operand's ID.
        """       
        return self._id
    
    def setID(self, id):
        """Sets the operand's ID.
        
        id: ~~ID - The operand's new ID.
        """
        self._id = id
        self._setValue(id)
        self._setType(id.type())

class TupleOperand(Operand):
    """Represents a tuple operand. For a TupleOperand, :meth:`value()` returns
    a list of the individual ~~Operand objects, and :meth:`type() returns a
    list of the individual operands' ~~Type objects.
    
    ops: list of ~~Operand - The individual operands of the tuple.
    location: ~~Location - A location to be associated with the operand. 
    """
    def __init__(self, ops, location=None):
        vals = ops
        types = [op.type() for op in ops]
        super(TupleOperand, self).__init__(vals, type.Tuple(types), location)
        self._ops = ops
    
    def setTuple(self, ops):
        """Set the operand's tuple.
        
        ops: tuple of ~~Operand - The new tuple of operands.
        """
        types = [op.type() for op in ops]
        self._setValue(ops)
        self._setType(type.Tuple(types))
        self._ops = ops
        
    def __str__(self):
        return "(%s)" % ", ".join([str(op) for op in self._ops])

class TypeOperand(Operand):
    """Represents a type as an operand. For a TypeOperand, :meth:`value()`
    returns the ~~Type the operand refers to, and :meth:`type() returns 
    a corresponding ~~TypeDeclType.
     
    t: ~~Type - The type the operand refers to. 
    location: ~~Location - A location to be associated with the operand. 
    """
    def __init__(self, t, location=None):
        super(TypeOperand, self).__init__(t, type.TypeDeclType(t), location)
    
    def __str__(self):
        return str(self.value())
    
class Signature:
    """Defines an instruction's signature. The signature includes the
    instruction's name as well as number and types of operands and target. The
    class is not supposed to be instantiated directly; instead, instances are
    implicitly created when using the :func:`instruction` decorator.
    
    name: string - The name of the instruction, i.e., the HILTI mnemonic.
    
    op1: ~~Type - The type of the instruction's first operand, or None if unused.
    op2: ~~Type - The type of the instruction's second operand, or None if unused.
    op3: ~~Type - The type of the instruction's third operand, or None if unused.
    target: ~~Type - The type of the instruction;s result, or None if unused.
    
    callback: function - The function will be called each time an
    ~~Instruction has been instantiated with this signature. The callback will
    receive the ~~Instruction as its only parameter and can modify it as needed.
    
    terminator: bool - True if the instruction is considered a block
    |terminator|.

    Note: The types for operands and target must be given as the corresponding
    ~~Type *classes*, not instances of thereof. If any of the types is a tuple
    of ~~Type classes, that indicates that any of the tuple's member is a
    valid type for the operand/target.
    """
    def __init__(self, name, op1=None, op2=None, op3=None, target=None, callback=None, terminator=False):
        self._name = name
        self._op1 = op1
        self._op2 = op2
        self._op3 = op3
        self._target = target
        self._callback = callback
        self._terminator = terminator
        
    def name(self):
        """Returns the name of the instruction defined by the signature.
        
        Returns: string - The instruction name.
        """
        return self._name
    
    def op1(self):
        """Returns the type of the instruction's first operand.
        
        Returns: ~~Type - The type of the operand, or None if unused.
        The type is a *class*, not an instance of thereof.
        """        
        return self._op1
    
    def op2(self):
        """Returns the type of the instruction's second operand.
        
        Returns: ~~Type - The type of the operand, or None if unused.
        The type is a *class*, not an instance of thereof.
        """        
        return self._op2
    
    def op3(self):
        """Returns the type of the instruction's third operand.
        
        Returns: ~~Type - The type of the operand, or None if unused.
        The type is a *class*, not an instance of thereof.
        """        
        return self._op3

    def target(self):
        """Returns the type of the instruction's result.
        
        Returns: ~~Type - The type of the result, or None if unused.
        The type is a *class*, not an instance of thereof.
        """        
        return self._target
    
    def callback(self):
        """Returns the signature's callback function.
        
        Returns: function - The callback function.
        """
        return self._callback
    
    def terminator(self):
        """Returns whether the signature's instruction is a |terminator|.
        
        Returns: bool - True if it is terminator instruction.
        """
        return self._terminator
        
    def __str__(self):
        target = "[%s] = " % self._target if self._target else ""
        op1 = " [%s]" % self._op1 if self._op1 else ""
        op2 = " [%s]" % self._op2 if self._op2 else ""
        op3 = " [%s]" % self._op3 if self._op3 else ""
        return "%s%s%s%s%s" % (target, self._name, op1, op2, op3)

def _make_ins_init(myclass):
    def ins_init(self, op1=None, op2=None, op3=None, target=None, location=None):
        super(self.__class__, self).__init__(op1, op2, op3, target, location)
        
    ins_init.myclass = myclass
    return ins_init
        
def instruction(name, op1=None, op2=None, op3=None, target=None, callback=None, terminator=False, location=None):
    """A *decorater* for classes derived from ~~Instruction. The decorator
    defines the new instruction's ~~Signature. The arguments correpond to
    those of the ~~Signature constructor."""
    def register(ins):
        global _Instructions
        ins._signature = Signature(name, op1, op2, op3, target, callback, terminator)
        d = dict(ins.__dict__)
        d["__init__"] = _make_ins_init(ins)
        newclass = builtin_type(ins.__name__, (ins.__base__,), d)
        _Instructions[name] = newclass
        return newclass
    
    return register

# Currently, "operator" is just an alias for "instruction".
operator = instruction
"""A *decorater* for classes derived from ~~Operator. The decorator
defines the new operators's ~~Signature. The arguments correpond to
those of the ~~Signature constructor."""

def overload(operator, op1, op2=None, op3=None, target=None):
    """A *decorater* for classes that provide type-specific overloading of an
    operator. The decorator defines the overloaded operator's ~~Signature. The
    arguments correpond to those of the ~~Signature constructor except for
    *operator* which must be a subclass of ~~Operator."""
    def register(ins):
        global _OverloadedOperators
        assert issubclass(operator, Operator)

        global _Instructions
        ins._signature = Signature(operator().name(), op1, op2, op3, target)
        d = dict(ins.__dict__)
        d["__init__"] = _make_ins_init(ins)
        newclass = builtin_type(ins.__name__, (ins.__base__,), d)
        
        idx = operator.__name__
        try:
            _OverloadedOperators[idx] += [ins._signature]
        except:
            _OverloadedOperators[idx] = [ins._signature]
            
        return newclass
    
    return register

_Instructions = {}    
_OverloadedOperators = {}

def getInstructions():
    """Returns a list of instructions. More precisely, the function returns a
    list of all classes decorated with either ~~Instruction or ~~operator;
    these classes will be all be derived from ~~Instruction and represent a
    complete enumeration of all instructions provided by the HILTI language.
    
    Returns: list of ~~Instruction-derived classes - The list of all
    instructions.
    """
    return _Instructions

def createInstruction(name, op1=None, op2=None, op3=None, target=None, location=None):
    """Instantiates a new instruction. 
    
    name: The name of the instruction to be instantiated; i.e., the mnemnonic
    as defined by a :meth:`instruction` decorator.
    
    op1: ~~Operand - The instruction's first operand, or None if unused.
    op2: ~~Operand - The instruction's second operand, or None if unused.
    op3: ~~Operand - The instruction's third operand, or None if unused.
    target: ~~IDOperand - The instruction's target, or None if unused.
    location: ~~Location - A location to be associated with the instruction. 
    """
    try:
        i = _Instructions[name](op1, op2, op3, target, location)
    except KeyError:
        return None

    return i

import sys    

def matchInstructionWithSignature(i, sig):
    """Checks whether an instruction matches a signature. 
    
    i: ~~Instruction - The instruction to check.
    sig: ~~Signature - The signature to check with. 
    
    Returns: (match, errormsg) - *match* is True if the instruction matches
    the signature, and False otherwise. If *match* is false, *errormsg*
    contains a string describing the mismatch in a way suitable to present to
    the user in an error message."""

    def checkOp(op, sig, tag):
        if sig and op == None and not type.isOptional(sig):
            return "%s missing" % tag

        if op and not sig:
            return "superfluous %s" % tag

        if op and sig:
            error = False
            if isinstance(op, TypeOperand):
                if op.value() != sig:
                    error = True
            
            elif op.type() != sig:
                error = True
                
            if error:
                return "type of %s does not match signature (expected %s, found %s) " % \
                    (tag, str(type.fmtTypeClass(sig)), str(op.type()))
            
        return None
        
    msg = checkOp(i.op1(), sig.op1(), "operand 1")
    if not msg:
        msg = checkOp(i.op2(), sig.op2(), "operand 2")
    if not msg:
        msg = checkOp(i.op3(), sig.op3(), "operand 3")
    if not msg:
        msg = checkOp(i.target(), sig.target(),"target")
        
    if not msg:
        return (True, "success")
    else:
        return (False, msg)

def findOverloadedOperator(op):
    """Returns the type-specific version of an overloaded operator. Based on
    an instance of ~~Operator, it will search all type-specific
    implementations (i.e., all ~~OverloadedOperators) and return the matching
    ones. 
    
    op: ~~Operator - The operator for which to return the type-specific version.
    
    Returns: (num, ~~OverloadedOperator) - *num* is the number of matches, and
    the second element of the tuple is first match or None if *num* is zero.
    """
    
    matches = []
    
    try:
        for sig in _OverloadedOperators[op.__class__.__name__]:
            (success, errormsg) = matchInstructionWithSignature(op, sig)
            if success:
                matches += [sig]
    except KeyError:
        pass

    if not matches:
        return (0, None)

    return (len(matches), matches[0])    
