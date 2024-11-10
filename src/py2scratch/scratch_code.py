import astroid, inspect, abc, random, typing

UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'
NUMBERS = '0123456789'

def gen_random_id(length: int = 10):
    return ''.join(random.choice(UPPERCASE + LOWERCASE + NUMBERS) for _ in range(length))

def sliding_win(iterable: typing.Iterable, n: int = 3):
    for i in range(len(iterable)-n+1):
        yield [iterable[j] for j in range(i, i+n)]


class PyToScratchError(Exception):
    """ A base error for the py2scratch project. """
class FuncNotFound(PyToScratchError):
    """ No FunctionDef is provided. """
class NoHatExists(PyToScratchError):
    """ There is no hat blocks with the specified name. """
    
class ScratchBlock:
    @abc.abstractmethod
    def json(self):
        ...
class Code(ScratchBlock):
    def __init__(self, blocks: ScratchBlock):
        self.blocks = blocks
    
    def json(self):
        return {block['id']: {i:block[i] for i in block if i != 'id'} for block in self.blocks.json()}

class GreenFlag(ScratchBlock):
    def __init__(self, *seq: list[ScratchBlock]):
        self.greenflag_id = gen_random_id()
        self.seq = seq
    
    def json(self):
        seq_json = [block.json() for block in self.seq]
        seq_ids = [self.greenflag_id, *[block['id'] for block in seq_json], None]
        for idx, [id_par, _, id_next] in enumerate(sliding_win(seq_ids, 3)):
            seq_json[idx]['parent'] = id_par
            seq_json[idx]['next'] = id_next
        seq_json = [{
            "opcode": "event_whenflagclicked",
            "id": self.greenflag_id,
            "next": seq_ids[1],
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 0,
            "y": 0
        }] + seq_json
        return seq_json

class Variable(ScratchBlock):
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        
    def json(self):
        return [12, self.name, self.id]

class List(ScratchBlock):
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        
    def json(self):
        return [13, self.name, self.id]

type ShadowBlocks = str | Variable | List
class Say(ScratchBlock):
    def __init__(self, msg: ShadowBlocks):
        self.msg = msg
    
    def json(self):
        msg = None
        if isinstance(self.msg, str):
            msg = [1, [10, self.msg]]
        elif isinstance(self.msg, Variable) or isinstance(self.msg, List):
            msg = [3, 'default', self.msg]
        else:
            msg = [1, [10, str(self.msg)]]
        return {
            "opcode": "looks_say",
            "id": gen_random_id(),
            "inputs": {
                "MESSAGE": msg
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }

def get_hat(func_name: str):
    match func_name.split('_')[1:]:
        case ['flag', 'clicked']:
            return GreenFlag
        case _:
            raise NoHatExists(f'Hat block does not exist or not yet implemented')

def handle_call(stmt: astroid.Call):
    match stmt.func.name:
        case 'print':
            if len(stmt.args) > 1:
                raise NotImplementedError("`print` statements can't handle more than 1 argument right now.")
            if stmt.keywords:
                raise NotImplementedError("Kwargs are not suppoted.")
            if not isinstance(stmt.args[0], astroid.Const):
                raise NotImplementedError("No variables yet. :(")
            return Say(stmt.args[0].value)

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
        raise NotImplementedError('Special Functions (My blocks) are not supported. sorgy :(')
    
    func_body = parse_tree.body
    scratch_body = []
    for expr in func_body:
        if not isinstance(expr, astroid.Expr):
            raise ValueError('If this error throws, You somehow defied Python\'s function syntax.')
        stmt = expr.value
        match stmt:
            case astroid.Call():
                scratch_body.append(handle_call(stmt))
            case astroid.Name():
                print("Name")
    
    scratch_tree = Code(hat(*scratch_body))
    return scratch_tree.json()
        

if __name__ == '__main__':
    def _flag_clicked(sprite):
        print("skibidi toietto")
        
    print(parse_func(_flag_clicked))
    # print(Code(GreenFlag(Say('hi!'))).json())
