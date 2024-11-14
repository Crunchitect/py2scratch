import abc, warnings, copy
from .utils import *
from ..errors import *

inline_blocks = []

all_variables = {}
all_lists = {}

all_variables_ref = []

class ScratchBlock:
    @abc.abstractmethod
    def json(self):
        ...

class ScratchBlockInline:
    @abc.abstractmethod
    def json(self):
        ...

class ScratchBlockRef(ScratchBlock):
    @abc.abstractmethod
    def refify(self):
        ...
    
    @abc.abstractmethod
    def json(self):
        ...
class Code(ScratchBlock):
    def __init__(self, blocks: ScratchBlock):
        self.blocks = blocks
    
    def json(self):
        return {block['id']: {i:block[i] for i in block if i != 'id'} for block in self.blocks.json()}

class ID:
    def __init__(self, id):
        self.id = id

class Hat(ScratchBlock):
    def __init__(self, hat_opcode: str, *seq: list[ScratchBlock]):
        self.hat_id = gen_random_id()
        self.hat_opcode = hat_opcode
        self.seq = seq
        self.queue = []
    
    def _conv(self, seq):
        converted = []
        for block in seq:
            match block:
                case ScratchBlock():
                    converted.append(block.json())
                case Ref():
                    for subblock in block.json():
                        converted.append(subblock)
        return converted
                
    def _link(self, seq):
        linked = seq
        seq_ids = [self.hat_id, *[block['id'] for block in seq], None]
        for idx, [id_par, _, id_next] in enumerate(sliding_win(seq_ids, 3)):
            if 'parent' not in linked[idx]:
                linked[idx]['parent'] = id_par
            if 'next' not in linked[idx]:
                linked[idx]['next'] = id_next
        return linked
    
    def _add_inline(self, seq):
        added_inline = seq
        global inline_blocks
        non_root_inline_blocks = 0
        for inline_block in inline_blocks:
            inline_block_id = inline_block.id
            for block in (seq + [i for i in inline_blocks if i != inline_block]):
                if inline_block_id in repr(block):
                    inline_block_json = inline_block.json()
                    inline_block_json['parent'] = block['id']
                    added_inline.append(inline_block_json)
                    non_root_inline_blocks += 1
                    break
        if non_root_inline_blocks < len(inline_blocks):
            raise NonRootInlineBlocks("Non Top-level parentless blocks detected. Likely an internal bug.")
        return added_inline
    
    def _add_hat(self, seq):
        first_block_id = seq[0]['id']
        return [{
            "opcode": self.hat_opcode,
            "id": self.hat_id,
            "next": first_block_id,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 0,
            "y": 0
        }] + seq
    
    def json(self):
        jsoned = []
        
        self.queue.append(copy.deepcopy(self.seq))
        while self.queue:
            converted = self._conv(self.queue[0])
            linked = self._link(converted)
            added_inline = self._add_inline(linked)
            jsoned.extend(added_inline)
            self.queue.pop(0)
        added_hat = self._add_hat(jsoned)
        
        return added_hat

class GreenFlag(Hat):
    def __init__(self, *seq):
        super().__init__('event_whenflagclicked', *seq)
    
    def json(self):
        return super().json()

class Variable(ScratchBlock):
    def __init__(self, name: str, idx: str):
        self.name = name
        self.id = idx
        all_variables[idx] = name
        all_variables_ref.append(self)
        
    def json(self):
        return [12, self.name, self.id]


class Ref:
    def __init__(self, cmds: list[ScratchBlock], ref: Variable):
        self.cmds = cmds
        self.ref = ref
    
    def json(self):
        return [cmd.json() for cmd in self.cmds]

class ID:
    def __init__(self, id):
        self.id = id

class List(ScratchBlock):
    def __init__(self, name: str, idx: str):
        self.name = name
        self.id = idx
        all_lists[idx] = name
        
    def json(self):
        return [13, self.name, self.idx]

class SetVariable(ScratchBlockRef):
    def __init__(self, var: Variable, val):
        self.var = var
        self.val = val
        self.id = gen_random_id()
    
    def refify(self):
        if isinstance(self.val, Ref):
            return Ref([*self.val.cmds, self], self.val.ref)
        else:
            return self
    
    def json(self):
        val = convert_inline_to_json(self.val)
        return {
            "opcode": "data_setvariableto",
            "id": self.id,
            "inputs": {
                "VALUE": val
            },
            "fields": {
                "VARIABLE": [ self.var.name, self.var.id ]
            },
            "shadow": False,
            "topLevel": False,
        }

type ShadowBlocks = str | Variable | List | Ref
class Say(ScratchBlockRef):
    def __init__(self, msg):
        self.msg = msg[0] if isinstance(msg, list) else msg
        self.id = gen_random_id()
    
    def refify(self):
        if isinstance(self.msg, Ref):
            return Ref([*self.msg.cmds, self], self.msg.ref)
        else:
            return self
    
    def json(self):
        msg = convert_inline_to_json(self.msg)
        return {
            "opcode": "looks_say",
            "id": self.id,
            "inputs": {
                "MESSAGE": msg
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }

class Answer(ScratchBlockInline):
    def __init__(self):
        global inline_blocks
        inline_blocks.append(self)
        self.id = gen_random_id()
    
    def json(self):
        return {
            "opcode": "sensing_answer",
            "next": None,
            "id": self.id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False
        }

class Ask(ScratchBlockRef):
    def __init__(self, question):
        # self.question = question
        self.question = question[0] if isinstance(question, list) else question
        self.id = gen_random_id()
    
    def refify(self):
        if isinstance(self.question, Ref):
            return Ref([*self.question.cmds, self], self.question.ref)
        else:
            return self
    
    def json(self):
        question = convert_inline_to_json(self.question)
        return {
            "opcode": "sensing_askandwait",
            "id": self.id,
            "inputs": {
                "QUESTION": question
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }

class BinOp(ScratchBlockRef):
    def __init__(self, op, left_attr, right_attr, left, right):
        self.id = gen_random_id()
        self.left = left
        self.right = right
        self.op = op
        self.left_attr = left_attr
        self.right_attr = right_attr
    
    def refify(self):
        cmds = []
        cmds.extend(self.left.cmds if isinstance(self.left, Ref) else [])
        cmds.extend(self.right.cmds if isinstance(self.right, Ref) else [])
        result = Variable(f'tmp-binop-{gen_random_id()}', gen_random_id())
        global inline_blocks
        inline_blocks.append(self)
        cmds.extend([SetVariable(result, ID(self.id))])
        return Ref(cmds, result)
    
    def json(self):
        left = convert_inline_to_json(self.left)
        right = convert_inline_to_json(self.right)
        return {
            "opcode": self.op,
            "next": None,
            "id": self.id,
            "inputs": {
                self.left_attr: left,
                self.right_attr: right
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }

class Add(BinOp):
    def __init__(self, left, right):
        super().__init__("operator_add", "NUM1", "NUM2", left, right)
        
class Sub(BinOp):
    def __init__(self, left, right):
        super().__init__("operator_subtract", "NUM1", "NUM2", left, right)

class Mul(BinOp):
    def __init__(self, left, right):
        super().__init__("operator_multiply", "NUM1", "NUM2", left, right)

class Join(BinOp):
    def __init__(self, left, right):
        super().__init__("operator_join", "STRING1", "STRING2", left, right)

def convert_inline_to_json(val):
    if isinstance(val, list) and type(val[0]) != int:
        val = val[0]
    match val:
        case ScratchBlock() | ScratchBlockRef():
            val = [3, val.json(), [10, 'default']]
        case Ref():
            val = [3, val.ref.json(), [10, 'default']]
        case ScratchBlockInline() | ID():
            val = [3, val.id, [10, 'default']]
        case str():
            val = [1, [10, val]]
        case int() | float():
            val = [1, [10, str(val)]]
        case _:
            warnings.warn(f"Unknown/Unsupported Type ({type(val)}) for variable {str(val)}, Assuming `str`")
            val = [1, [10, repr(val)]]
    return val
