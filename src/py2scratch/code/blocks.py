import abc, warnings
from .utils import *
from ..errors import *

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

class ID:
    def __init__(self, id):
        self.id = id

class GreenFlag(ScratchBlock):
    def __init__(self, *seq: list[ScratchBlock]):
        self.greenflag_id = gen_random_id()
        self.seq = seq
    
    def json(self):
        seq_json = [block.json() for block in self.seq]
        flattened_seq_json = []
        # Flatten 1-layer.
        for terms in seq_json:
            if isinstance(terms, list):
                for term in terms:
                    flattened_seq_json.append(term)
            else:
                flattened_seq_json.append(terms)
        linked_seq_json = flattened_seq_json
        seq_ids = [self.greenflag_id, *[block['id'] for block in flattened_seq_json], None]
        for idx, [id_par, _, id_next] in enumerate(sliding_win(seq_ids, 3)):
            if 'parent' not in linked_seq_json[idx]:
                linked_seq_json[idx]['parent'] = id_par
            if 'next' not in linked_seq_json[idx]:
                linked_seq_json[idx]['next'] = id_next
        
        complete_seq_json = linked_seq_json
        
        from .pyparser import get_orphans
        # Adopt the orphans.
        orphans = get_orphans()
        adopted_count = 0
        for orphan in orphans:
            print("!")
            orphan_id = orphan.json()['id']
            for block in linked_seq_json:
                # Janky, but works.
                if orphan_id in repr(block):
                    orphan_json = orphan.json()
                    orphan_json['parent'] = block['id']
                    complete_seq_json.append(orphan_json)
                    adopted_count += 1
                    break
        if adopted_count < len(orphans):
            return TooManyOrphans("Non Top-level parentless blocks detected. Likely an internal bug.")
        
        hatted_seq_json = [{
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
        }] + linked_seq_json
        return hatted_seq_json

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
        val = None
        match self.val:
            case ScratchBlock() | ScratchBlockRef():
                val = [3, self.val.json(), [10, 'default']]
            case Ref():
                val = [3, self.val.ref.json(), [10, 'default']]
            case ID():
                val = [3, self.val.id, [10, 'default']]
            case str():
                val = [1, [10, self.val]]
            case int() | float():
                val = [1, [10, str(self.val)]]
            case _:
                warnings.warn(f"Unknown/Unsupported Type ({type(self.val)}) for variable {repr(self.val)}, Assuming `repr`")
                val = [1, [10, repr(self.val)]]
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
        match self.msg:
            case str():
                self.msg = [1, [10, self.msg]]
            case list():
                ...
            case ScratchBlock() | ScratchBlockRef():
                self.msg = [3, self.msg.json(), [10, 'default']]
            case ID():
                self.msg = [3, self.msg.id, [10, 'default']]
            case Ref():
                self.msg = [3, self.msg.ref.json(), [10, 'default']]
            case _:
                self.msg = [1, [10, str(self.msg)]]
        return {
            "opcode": "looks_say",
            "id": self.id,
            "inputs": {
                "MESSAGE": self.msg
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }

class Answer(ScratchBlock):
    def __init__(self):
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
        match self.question:
            case str():
                self.question = [1, [10, self.question]]
            case list():
                ...
            case ScratchBlock() | ScratchBlockRef():
                self.question = [3, self.question.json(), [10, 'default']]
            case Ref():
                self.question = [3, self.question.ref.json(), [10, 'default']]
            case _:
                self.question = [1, [10, str(self.question)]]
        return {
            "opcode": "sensing_askandwait",
            "id": self.id,
            "inputs": {
                "QUESTION": self.question
            },
            "fields": {},
            "shadow": False,
            "topLevel": False
        }
