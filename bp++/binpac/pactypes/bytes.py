# $Id$
#
# The bytes type.

import binpac.type as type
import binpac.expr as expr
import binpac.grammar as grammar
import binpac.operator as operator

import hilti.type
import hilti.operand

@type.pac(None)
class IteratorBytes(type.Iterator):
    """Type for ``iterator<bytes>``.

    location: ~~Location - The location where the type was defined.
    """
    def __init__(self, location=None):
        super(IteratorBytes, self).__init__(type.Bytes())

    # Overwritten from Iterator.

    def derefType(self):
        return type.SignedInteger(8)

    def hiltiType(self, cg):
        return hilti.type.IteratorBytes()

@type.pac("bytes")
class Bytes(type.ParseableType, type.Iterable, type.Sinkable):
    """Type for bytes objects.

    location: ~~Location - A location object describing the point of definition.
    """
    def __init__(self, location=None):
        super(Bytes, self).__init__(location=location)

    ### Overridden from Type.

    def name(self):
        return "bytes"

    def validateInUnit(self, field, vld):
        # We need exactly one of the attributes.
        c = 0
        for (name, (ty, const, default)) in self.supportedAttributes().items():
            if self.hasAttribute(name) and not name in ("default", "convert"):
                c += 1

        if c == 0:
            vld.error(field, "bytes type needs a termination attribute")

        if c > 1:
            vld.error(field, "bytes type accepts exactly one termination attribute")

    def validateCtor(self, vld, value):
        if not isinstance(value, str) and not isinstance(value, unicode):
            vld.error(self, "bytes: ctor of wrong internal type %s" % repr(value))

    def hiltiCtor(self, cg, val):
        return hilti.operand.Ctor(val, hilti.type.Reference(hilti.type.Bytes()))

    def hiltiType(self, cg):
        return hilti.type.Reference(hilti.type.Bytes())

    def hiltiDefault(self, cg, must_have=True):
        if not must_have:
            return None

        return hilti.operand.Ctor("", self.hiltiType(cg))

    def pac(self, printer):
        printer.output("bytes")

    def pacCtor(self, printer, value):
        printer.output("b\"%s\"" % value)

    ### Overridden from Iterable.

    def iterType(self):
        return IteratorBytes()

    ### Overridden from ParseableType.

    def supportedAttributes(self):
        return {
            "default": (self, True, None),
            "convert": (type.Any(), False, None),
            "length": (type.UnsignedInteger(64), False, None),
            "until": (type.Bytes(), False, None),
            "eod": (None, False, None),
            }

    def production(self, field):
        filter = self.attributeExpr("convert")
        return grammar.Variable(None, self, filter=filter, field=field, location=self.location())

    def productionForLiteral(self, field, literal):
        filter = self.attributeExpr("convert")
        return grammar.Literal(None, literal, field=field, filter=filter)

    def fieldType(self):
        filter = self.attributeExpr("convert")
        if filter:
            return filter.type().resultType()
        else:
            return self.parsedType()

    def generateParser(self, cg, var, cur, dst, skipping):

        def toSink(data):
            if not var.field():
                return

            sink = var.field().sink()

            if not sink:
                return

            self.hiltiWriteDataToSink(cg, sink, data)

        if var.field() and var.field().sink():
            # Need data if not skipping.
            skipping = False

        bytesit = hilti.type.IteratorBytes(hilti.type.Bytes())
        resultt = hilti.type.Tuple([self.hiltiType(cg), bytesit])
        fbuilder = cg.functionBuilder()

        # FIXME: We trust here that bytes iterators are inialized with the
        # generic end position. We should add a way to get that position
        # directly (but without a bytes object).
        end = fbuilder.addTmp("__end", bytesit)

        op1 = cg.builder().tupleOp([cur, end])
        op2 = None
        op3 = None

        if self.hasAttribute("length"):
            op2 = cg.builder().idOp("Hilti::Packed::BytesFixed" if not skipping else "Hilti::Packed::SkipBytesFixed")
            expr = self.attributeExpr("length").coerceTo(type.UnsignedInteger(64), cg)
            op3 = expr.evaluate(cg)

        elif self.hasAttribute("until"):
            op2 = cg.builder().idOp("Hilti::Packed::BytesDelim" if not skipping else "Hilti::Packed::SkipBytesDelim")
            expr = self.attributeExpr("until").coerceTo(type.Bytes(), cg)
            op3 = expr.evaluate(cg)

        elif self.hasAttribute("eod"):

            loop = fbuilder.newBuilder("eod_loop")
            done = fbuilder.newBuilder("eod_reached")
            suspend = fbuilder.newBuilder("eod_not_reached")

            cg.builder().jump(loop.labelOp())

            eod = fbuilder.addTmp("__eod", hilti.type.Bool())
            loop.bytes_is_frozen(eod, cur)
            loop.if_else(eod, done.labelOp(), suspend.labelOp())

            cg.setBuilder(suspend)
            cg.generateInsufficientInputHandler(cur)
            cg.builder().jump(loop.labelOp())

            cg.setBuilder(done)
            if not skipping:
                done.bytes_sub(dst, cur, end)
                toSink(dst)

            return end

        result = self.generateUnpack(cg, op1, op2, op3)

        builder = cg.builder()

        if dst and not skipping:
            builder.tuple_index(dst, result, builder.constOp(0))
            toSink(dst)

        builder.tuple_index(cur, result, builder.constOp(1))

        return cur

@operator.Size(Bytes)
class _:
    def type(e):
        return type.UnsignedInteger(64)

    def simplify(e):
        if e.isInit():
            n = len(e.value())
            return expr.Ctor(n, type.UnsignedInteger(64))

        else:
            return None

    def evaluate(cg, e):
        tmp = cg.functionBuilder().addLocal("__size", hilti.type.Integer(64))
        cg.builder().bytes_length(tmp, e.evaluate(cg))
        return tmp

@operator.Equal(Bytes, Bytes)
class _:
    def type(e1, e2):
        return type.Bool()

    def simplify(e1, e2):
        if not e1.isInit() or not e2.isInit():
            return None

        b = (e1.value() == e2.value())
        return expr.Ctor(b, type.Bool())

    def evaluate(cg, e1, e2):
        tmp = cg.functionBuilder().addLocal("__equal", hilti.type.Bool())
        cg.builder().equal(tmp, e1.evaluate(cg), e2.evaluate(cg))
        return tmp

@operator.Plus(Bytes, Bytes)
class Plus:
    def type(e1, e2):
        return type.Bytes()

    def simplify(e1, e2):
        if not e1.isInit() or not e2.isInit():
            return None

        b = (e1.value() + e2.value())
        return expr.Ctor(b, type.Bytes())

    def evaluate(cg, e1, e2):
        tmp = cg.functionBuilder().addLocal("__copy", e1.type().hiltiType(cg))
        cg.builder().bytes_copy(tmp, e1.evaluate(cg))
        cg.builder().bytes_append(tmp, e2.evaluate(cg))
        return tmp

@operator.PlusAssign(Bytes, Bytes)
class Plus:
    def type(e1, e2):
        return type.Bytes()

    def evaluate(cg, e1, e2):
        e1 = e1.evaluate(cg)
        cg.builder().bytes_append(e1, e2.evaluate(cg))
        return e1

@operator.MethodCall(type.Bytes, expr.Attribute("match"), [type.RegExp, operator.Optional(type.UnsignedInteger)])
class Match:
    def type(obj, method, args):
        return type.Bytes()

    def evaluate(cg, obj, method, args):
        obj = obj.evaluate(cg)
        re = args[0].evaluate(cg)

        if len(args) > 1:
            group = args[1].evaluate(cg)
        else:
            group = cg.builder().constOp(0)

        func = cg.builder().idOp("BinPACIntern::bytes_match")
        args = cg.builder().tupleOp([obj, re, group])
        tmp = cg.functionBuilder().addLocal("__match", obj.type())
        cg.builder().call(tmp, func, args)
        return tmp

@operator.MethodCall(type.Bytes, expr.Attribute("startswith"), [type.Bytes])
class StartsWith:
    def type(obj, method, args):
        return type.Bool()

    def evaluate(cg, obj, method, args):
        obj = obj.evaluate(cg)
        pattern = args[0].evaluate(cg)

        func = cg.builder().idOp("Hilti::bytes_starts_with")
        args = cg.builder().tupleOp([obj, pattern])
        tmp = cg.functionBuilder().addLocal("__starts", hilti.type.Bool())
        cg.builder().call(tmp, func, args)
        return tmp

@operator.MethodCall(type.Bytes, expr.Attribute("begin"), [])
class Begin:
    def type(obj, method, args):
        return obj.type().iterType()

    def evaluate(cg, obj, method, args):
        tmp = cg.functionBuilder().addLocal("__iter", obj.type().iterType().hiltiType(cg))
        cg.builder().begin(tmp, obj.evaluate(cg))
        return tmp

@operator.MethodCall(type.Bytes, expr.Attribute("end"), [])
class End:
    def type(obj, method, args):
        return obj.type().iterType()

    def evaluate(cg, obj, method, args):
        tmp = cg.functionBuilder().addLocal("__iter", obj.type().iterType().hiltiType(cg))
        cg.builder().end(tmp, obj.evaluate(cg))
        return tmp


