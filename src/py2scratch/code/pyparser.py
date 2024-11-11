import astroid
from . import blocks
from .utils import gen_random_id

defined_functions = []
orphans: list[blocks.ScratchBlock | blocks.ScratchBlockRef] = []

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
            print("input!")
            if len(stmt.args) > 1:
                raise SyntaxError(f"`input` statements take 1 argument. {len(stmt.args)} provided.")
            prompt = stmt.args[0]
            var = blocks.Variable(f'tmp-ret-{gen_random_id()}', gen_random_id())
            answer_stmt = blocks.Answer()
            orphans.append(answer_stmt)
            return blocks.Ref([
                blocks.Ask(handle_expr(prompt)).refify(),
                blocks.SetVariable(var, blocks.ID(answer_stmt.id)).refify()
            ], var)
        case _:
            return None

def handle_const(value: astroid.Const):
    return value.value

def handle_expr(expr: astroid.Expr):
    match expr:
        case astroid.Expr():
            return handle_expr(expr.value)
        case astroid.Const():
            return handle_const(expr)
        case astroid.Call():
            return handle_call(expr)
        case astroid.Name():
            return [blocks.Variable(expr.name, gen_random_id())]
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

def get_orphans():
    return orphans

def unref(stmt: blocks.ScratchBlock | blocks.Ref):
    ref = stmt
    if isinstance(stmt, blocks.Ref):
        ref = ref.cmds
    return ref
