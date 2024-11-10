import abc
import dataclasses
from py2scratch.code.utils import *

all_variables = {}
all_lists = {}

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
    def __init__(self, name: str, idx: str):
        self.name = name
        self.id = idx
        all_variables[idx] = name
        
    def json(self):
        return [12, self.name, self.id]

    
@dataclasses.dataclass
class Ref:
    cmds: list[ScratchBlock]
    ref: Variable

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
class Say(ScratchBlock):
    def __init__(self, msg: ShadowBlocks):
        self.msg = msg
    
    def json(self):
        msg = None
        if isinstance(self.msg, list):
            msg = self.msg[0]
        else:
            msg = self.msg
        
        if isinstance(msg, str):
            msg = [1, [10, msg]]
        elif isinstance(msg, Variable) or isinstance(msg, List):
            # print(msg.json(), 'i')
            msg = [3, msg.json(), [10, 'default']]
        elif isinstance(msg, Ref):
            msg = [3, msg.ref.json(), [10, 'default']]
        else:
            msg = [1, [10, str(msg)]]
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
