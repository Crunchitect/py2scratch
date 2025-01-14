import astroid, inspect, typing
from .errors import *
from .code.blocks import *
from .code.pyparser import *

def get_hat(func_name: str):
    match func_name.split('_')[1:]:
        case ['flag', 'clicked']:
            return GreenFlag
        case _:
            raise NoHatExists(f'Hat block does not exist or not yet implemented')

def parse_func(func: typing.Callable):
    try:
        src = inspect.getsource(func)
        parse_tree = astroid.parse(src).body[0]
    except TypeError | AttributeError:
        raise FuncNotFound('Code must be a `def` function definition (FunctionDef)!')
    if not isinstance(parse_tree, astroid.FunctionDef):
        raise FuncNotFound('Code must be a `def` function definition (FunctionDef)!')
    
    scratch_tree = None
    
    # Check if is a valid hat.
    func_name = parse_tree.name
    sprite_inst_name = parse_tree.args.args[0].name
    hat = None
    if func_name.startswith('_'):
        hat = get_hat(func_name)
    else:
        raise NotImplementedError(f"No custom functions support yet. Defined {func_name}")
    
    func_body = parse_tree.body                                                                                                                                                                                                                                                                     
    scratch_body = []
    for stmt in func_body:
        scratch_body += unref(handle_stmt(stmt))
    
    scratch_tree = Code(hat(*scratch_body))
    print(scratch_tree.json())
    return scratch_tree.json()
        

if __name__ == '__main__':
    def _flag_clicked(sprite):
        x = print('hi!')
        print(x)
        
    print(parse_func(_flag_clicked))
    # print(Code(GreenFlag(Say('hi!'))).json())
