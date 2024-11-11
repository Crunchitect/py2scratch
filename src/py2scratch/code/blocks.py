import abc
from py2scratch.code.utils import *

all_variables = {}
all_lists = {}

class ScratchBlock:
    @abc.abstractmethod
    def json(self):
        ...

class ScratchBlockRef:
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

class GreenFlag(ScratchBlock):
    def __init__(self, *seq: list[ScratchBlock]):
        self.greenflag_id = gen_random_id()
        self.seq = seq
    
    def json(self):
        seq_json = [block.json() for block in self.seq]
        flattened_seq_json = []
        for terms in seq_json:
            # for Refs.
            if isinstance(terms, list):
                for term in terms:
                    flattened_seq_json.append(term)
            # for everything else.
            else:
                flattened_seq_json.append(terms)
        # print("BRO?!",self.seq, seq_json)
        seq_ids = [self.greenflag_id, *[block['id'] for block in flattened_seq_json], None]
        for idx, [id_par, _, id_next] in enumerate(sliding_win(seq_ids, 3)):
            flattened_seq_json[idx]['parent'] = id_par
            flattened_seq_json[idx]['next'] = id_next
        flattened_seq_json = [{
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
        }] + flattened_seq_json
        return flattened_seq_json

class Variable(ScratchBlock):
    def __init__(self, name: str, idx: str):
        self.name = name
        self.id = idx
        all_variables[idx] = name
        
    def json(self):
        return [12, self.name, self.id]


class Ref:
    def __init__(self, cmds: list[ScratchBlock], ref: Variable):
        self.cmds = cmds
        self.ref = ref
    
    def json(self):
        return [cmd.json() for cmd in self.cmds]

class List(ScratchBlock):
    def __init__(self, name: str, idx: str):
        self.name = name
        self.id = idx
        all_lists[idx] = name
        
    def json(self):
        return [13, self.name, self.idx]

class SetVariable(ScratchBlock):
    def __init__(self, var: Variable, val):
        self.var = var
        self.val = val
    
    def json(self):
        val = None
        if isinstance(self.val, Variable):
            val = [3, self.val.json(), [10, 'default']]
        elif isinstance(self.val, Ref):
            val = [3, self.val.ref.json(), [10, 'default']]
        else:
            val = [1, [10, str(self.val)]]
        return {
            "opcode": "data_setvariableto",
            "id": gen_random_id(),
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
    def __init__(self, msg: ShadowBlocks):
        self.msg = msg[0] if isinstance(msg, list) else msg
    
    def refify(self):
        if isinstance(self.msg, Ref):
            return Ref([*self.msg.cmds, self], self.msg.ref)
        else:
            return self
    
    def json(self):
        match self.msg:
            case str():
                self.msg = [1, [10, self.msg]]
            case Variable() | List():
                self.msg = [3, self.msg.json(), [10, 'default']]
            case Ref():
                self.msg = [3, self.msg.ref.json(), [10, 'default']]
            case _:
                self.msg = [1, [10, str(self.msg)]]
        return {
            "opcode": "looks_say",
            "id": gen_random_id(),
            "inputs": {
                "MESSAGE": self.msg
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }
