import json, hashlib, os, sys, pathlib, zipfile, io, warnings, mutagen
from functools import reduce
from typing import NamedTuple, Callable
from py2scratch.scratch_code import parse_func
from py2scratch.errors import *
from PIL import Image

type ScratchObj = Sprite | Stage
FileData = NamedTuple('FileData', [('ext', str), ('data', bytes), ('hash', str)])
main_dir = os.path.dirname(sys.argv[0])

data: list[FileData] = []

class Project:
    def __init__(self, dependencies: list[ScratchObj] = []):
        self.dependencies = dependencies
    
    def add(self, obj):
        self.dependencies.append(obj)
    
    def build(self, filename: str = 'output.sb3'):
        extensions = []
        targets = []
        monitors = []
        meta = {'semver': '3.0.0', 'vm': '2.3.4', 'agent': 'Py2Scratch'}
        
        for dependency in self.dependencies:
            match dependency:
                case Stage():
                    from py2scratch.code.blocks import all_variables
                    dependency.variables = {k: [v, ""] for k, v in all_variables.items()}
                    if not dependency.costumes:
                        raise NoCostumeProvided(f'{dependency.name} must have at least 1 costume!')
                    targets.append(dependency.json())
                case Sprite():
                    if not dependency.costumes:
                        raise NoCostumeProvided(f'{dependency.name} must have at least 1 costume!')
                    targets.append(dependency.json())
        
        project_json = json.dumps({
            'extensions': extensions,
            'targets': targets,
            'monitors': monitors,
            'meta': meta
        })

        zip_dir = (pathlib.Path(main_dir) / filename).resolve()
        
        with zipfile.ZipFile(zip_dir, 'w') as f:
            for file in data:
                f.writestr(file.hash + '.' + file.ext, file.data)
            f.writestr('project.json', project_json)


class Target:
    def __init__(self, name: str, z: int = 1) -> None:
        self.name = name
        
        self.current_costume = 1
        self.layer_order = z
        self.volume = 100
        
        self.variables = {}
        self.lists = {}

        self.costumes: list[Costume] = []
        self.sounds: list[Sound] = []
        self.funcs: list[Callable] = []
    
    def json(self):
        scratch_code_data = reduce(lambda a, b: a | b, (parse_func(func) for func in self.funcs), {})
        return {
            'variables': self.variables,
            'lists': self.lists,
            'broadcasts': {},
            'blocks': scratch_code_data,
            'comments': {},
            'costumes': [costume.json() for costume in self.costumes],
            'sounds': [sound.json() for sound in self.sounds],
            'currentCostume': self.current_costume,
            'layerOrder': self.layer_order,
            'volume': self.volume
        }

class RotationStyles:
    ALL_AROUND = 'all around'
    LEFT_RIGHT = 'left-right'
    NONE = 'don\'t rotate'

class Sprite(Target):
    def __init__(self,
                 name: str,
                 z: int = 1, visible: bool = True, x: float = 0, y: float = 0,
                 rotation: float = 90, rotation_style: str = RotationStyles.ALL_AROUND, scale: float = 100,
                 draggable: bool = False):
        self.name = name
        self.layer_order = z
        self.current_costume = 1
        self.volume = 100
        
        self.variables = {}
        self.lists = {}
        
        self.x = x
        self.y = y
        self.rotation = rotation
        self.rotation_style = rotation_style
        self.scale = scale
        self.draggable = draggable
        self.visible = visible
        
        self.costumes: list[Costume] = []
        self.sounds: list[Sound] = []
        self.funcs: list[Callable] = []
        
    def json(self):
        target_json = super().json()
        target_json['isStage'] = False
        target_json['name'] = self.name
        target_json['x'] = self.x
        target_json['y'] = self.y
        target_json['visible'] = self.visible
        target_json['direction'] = self.rotation
        target_json['rotationStyle'] = self.rotation_style
        target_json['scale'] = self.scale
        target_json['draggable'] = self.draggable
        return target_json

class Stage(Target):
    def __init__(self) -> None:
        super().__init__('Stage', 0)
    
    def json(self):
        target_json = super().json()
        target_json['isStage'] = True
        target_json['name'] = 'Stage'
        return target_json


class Asset:
    def __init__(self, name: str, path: os.PathLike) -> None:
        global data
        
        self.name = name
        self.path = path
        self.filename, self.extension = path.rsplit('/', 1)[1].rsplit('.')
        
        asset_path = (pathlib.Path(main_dir) / path).resolve()
        
        self.data = bytes()
        with open(asset_path, "rb") as f:
            self.data = f.read()
        self.hash = hashlib.md5(self.data).hexdigest()

        data.append(FileData(ext=self.extension, data=self.data, hash=self.hash))
    
    def json(self):
        return {
            'assetId': self.hash,
            'name': self.name,
            'md5ext': self.hash + '.' + self.extension,
            'dataFormat': self.extension,   
        }

class Costume(Asset):
    def json(self):
        asset_json = super().json()
        asset_json['bitmapResolution'] = 1
        try:
            image = Image.open(io.BytesIO(self.data))
            asset_json['rotationCenterX'] = image.width // 2
            asset_json['rotationCenterY'] = image.height // 2
        except:
            image = None
            warnings.warn("WARNING: Pillow does not support SVG centering, Your vector sprite might not be centered", ResourceWarning)
            asset_json['rotationCenterX'] = 0
            asset_json['rotationCenterY'] = 0
        return asset_json


class Sound(Asset):
    def json(self):
        asset_json = super().json()
        asset_json['bitmapResolution'] = 1
        try:
            soundtrack = mutagen.File(io.BytesIO(self.data))
            sound_info = soundtrack.info
            asset_json['rate'] = sound_info.sample_rate
            asset_json['sampleCount'] = round(sound_info.sample_rate * sound_info.length)
        except:
            raise InvalidAudioFile("Please pass in a proper audio file!")
        return asset_json