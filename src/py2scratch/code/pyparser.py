import astroid
import py2scratch.code.blocks as blocks
from py2scratch.code.utils import gen_random_id

defined_functions = []

def handle_call(stmt: astroid.Call):
    if stmt.func.name in defined_functions:
        raise NotImplementedError("No custom functions support yet.")
    func = handle_builtins(stmt)
    if func is None:
        raise NotImplementedError("No custom functions support yet.")
    return func

def handle_builtins(stmt: astroid.Call):
    match stmt.func.name:
        case 'print':
            if len(stmt.args) > 1:
                raise NotImplementedError("`print` statements can't handle more than 1 argument right now.")
            if stmt.keywords:
                raise NotImplementedError("Kwargs are not suppoted.")
            var = blocks.Variable(f'tmp-{gen_random_id()}', gen_random_id())
            return blocks.Ref([
                blocks.SetVariable(var, ""),
                blocks.Say(handle_expr(stmt.args[0]))
            ], var)
        case _:
            return None

def handle_const(value: astroid.Const):
    return value.value

def handle_expr(expr: astroid.Expr):
    match expr:
        case astroid.Expr():
            return handle_expr(expr.value)
        # case str() | int() | float():
        #     return expr
        case astroid.Const():
            return handle_const(expr)
        case astroid.Call():
            return handle_call(expr)
        case astroid.Name():
            return [blocks.Variable(expr.name, gen_random_id())]
        case _:
            raise NotImplementedError(f"Nothing but expressions are implemented ({expr}). Sorry :(")

def handle_assign(stmt: astroid.Assign):
    if len(stmt.targets) > 1:
        raise NotImplementedError("Sorry, Unpacking is unsupported.")
    tmp = blocks.Variable(stmt.targets[0].name, gen_random_id())
    return [blocks.SetVariable(tmp, handle_expr(stmt.value))]

def handle_stmt(stmt: astroid.NodeNG):
    match stmt:
        case astroid.Expr():
            return handle_expr(stmt)
        case astroid.Assign():
            return handle_assign(stmt)
        case _:
            raise NotImplementedError(f"Nothing but expressions are implemented ({stmt}). Sorry :(")

def unref(stmt: blocks.ScratchBlock | blocks.Ref):
    ref = stmt
    if isinstance(stmt, blocks.Ref):
        ref = ref.cmds
    return ref
