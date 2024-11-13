import astroid, warnings
from . import blocks
from .utils import gen_random_id
from ..errors import *

defined_functions = []

def handle_call(stmt: astroid.Call):
    if stmt.func.name in defined_functions:
        raise NotImplementedError(f"No custom functions support yet. Called {stmt.func.name}")
    func = handle_builtins(stmt)
    if func is None:
        raise NotImplementedError(f"Function is not implemented, or does not exist.")
    return func

def handle_builtins(stmt: astroid.Call):
    match stmt.func.name:
        case 'print':
            if len(stmt.args) > 1:
                raise NotImplementedError(f"`print` statements can't handle more than 1 argument right now. {len(stmt.args)} provided.")
            if stmt.keywords:
                raise NotImplementedError(f"Kwargs are not suppoted. {stmt.keywords} provided.")
            var = blocks.Variable(f'tmp-ret-{gen_random_id()}', gen_random_id())
            return blocks.Ref([
                blocks.SetVariable(var, "").refify(),
                blocks.Say(handle_expr(stmt.args[0])).refify()
            ], var)
        case 'input':
            if len(stmt.args) > 1:
                raise SyntaxError(f"`input` statements take 1 argument. {len(stmt.args)} provided.")
            prompt = stmt.args[0]
            var = blocks.Variable(f'tmp-ret-{gen_random_id()}', gen_random_id())
            answer_stmt = blocks.Answer()
            return blocks.Ref([
                blocks.Ask(handle_expr(prompt)).refify(),
                blocks.SetVariable(var, answer_stmt).refify()
            ], var)
        case 'str':
            return handle_expr(stmt.args[0])
        case _:
            return None

def handle_name(expr: astroid.Name):
    idx = [ref.name for ref in blocks.all_variables_ref].index(expr.name)
    return [blocks.Variable(blocks.all_variables_ref[idx].name, blocks.all_variables_ref[idx].id)]

def handle_const(value: astroid.Const):
    if isinstance(value.value, (str, float, int, bool)):
        return value.value
    if isinstance(value.value, list):
        raise NotImplementedError("Lists are not implemented yet.")
    raise NotImplementedError("Type not supported.")

class BinOp:
    @staticmethod
    def check_type(left: astroid.Expr, right: astroid.Expr):
        try:
            left_type = [type(inferred.value) for inferred in left.infer()]
            right_type = [type(inferred.value) for inferred in right.infer()]
            
            if not all([x == left_type[0] for x in left_type]):
                warnings.warn("{left} not static. Assuming `float`")
                left_type = float
            else:
                left_type = left_type[0]
            if not all([x == right_type[0] for x in right_type]):
                warnings.warn("{right} not static. Assuming `float`")
                right_type = float
            else:
                right_type = right_type[0]
            return left_type, right_type
        except astroid.AstroidError:
            raise TypeUninferrable(f"Can't infer type from {left} + {right}")
    
    @staticmethod
    def handle_add(left: astroid.Expr, right: astroid.Expr):
        left_type, right_type = BinOp.check_type(left, right)
        
        if left_type != right_type:
            raise TypeError(f"Can't do addition with '{left_type}' and '{right_type}'")
        
        if left_type in [int, float]:
            return [blocks.Add(handle_expr(left), handle_expr(right)).refify()]
        elif left_type == str:
            return [blocks.Join(handle_expr(left), handle_expr(right)).refify()]
        else:
            raise NotImplementedError(f"Addition of type {left_type} is not supported.")
    
    @staticmethod
    def handle_sub(left: astroid.Expr, right: astroid.Expr):
        left_type, right_type = BinOp.check_type(left, right)
        
        if left_type not in [int, float] or right_type not in [int, float]:
            raise SyntaxError(f"Can't do subtraction with '{left}' and '{right}'.")
        else:
            return [blocks.Sub(handle_expr(left), handle_expr(right)).refify()]

def handle_binop(expr: astroid.BinOp):
    binary_operators = ['+', '-', '*', '@', '/', '%', '**', '<<', '>>', '|', '^', '&', '//']
    if expr.op not in binary_operators:
        raise SyntaxError(f'{expr.op!r} is not a valid operator.')
    match expr.op:
        case '+':
            return BinOp.handle_add(expr.left, expr.right)
        case '-':
            return BinOp.handle_sub(expr.left, expr.right)
        case _:
            raise NotImplementedError(f"Operator '{expr.op}' is not implemented yet.")

def handle_expr(expr: astroid.Expr):
    match expr:
        case astroid.Expr():
            return handle_expr(expr.value)
        case astroid.Const():
            return handle_const(expr)
        case astroid.Call():
            return handle_call(expr)
        case astroid.Name():
            return handle_name(expr)
        case astroid.BinOp():
            return handle_binop(expr)
        case _:
            raise NotImplementedError(f"{type(expr)} expressions are still unsupported currently. {expr} provided.")

def handle_assign(stmt: astroid.Assign):
    if len(stmt.targets) > 1:
        raise NotImplementedError("Unpacking assignments is currently unsupported.")
    tmp = blocks.Variable(stmt.targets[0].name, gen_random_id())
    return [blocks.SetVariable(tmp, handle_expr(stmt.value)).refify()]

def handle_stmt(stmt: astroid.NodeNG):
    match stmt:
        case astroid.Expr():
            return handle_expr(stmt)
        case astroid.Assign():
            return handle_assign(stmt)
        case _:
            raise NotImplementedError(f"{type(stmt)} Statements are still unsupported currently. {stmt} provided.")

def unref(stmt: blocks.ScratchBlock | blocks.Ref):
    ref = stmt
    if isinstance(stmt, blocks.Ref):
        ref = ref.cmds
    return ref
