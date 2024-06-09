import json, hashlib, os, inspect, pathlib, zipfile, io, warnings
from typing import NamedTuple
from PIL import Image

type ScratchObj = Sprite | Stage
FileData = NamedTuple('FileData', [('ext', str), ('data', bytes), ('hash', str)])

data: list[FileData] = []

class Project:
    def __init__(self, dependencies: list[ScratchObj] = []):
        self.dependencies = dependencies
    
    def add(self, obj):
        self.dependencies.append(obj)
    
    def build(self):
        extensions = []
        targets = []
        monitors = []
        meta = {'semver': '3.0.0', 'vm': '2.3.4', 'agent': 'Py2Scratch'}
        
        for dependency in self.dependencies:
            match dependency:
                case Target():
                    if not dependency.costumes:
                        raise ValueError(f'{dependency.name} must have at least 1 costume!')
                    targets.append(dependency.json())
        
        project_json = json.dumps({
            'extensions': extensions,
            'targets': targets,
            'monitors': monitors,
            'meta': meta
        })
        
        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0])
        main_dir = os.path.dirname(os.path.abspath(caller_module.__file__))
        zip_dir = (pathlib.Path(main_dir) / 'output.sb3').resolve()
        
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

        self.costumes: list[Costume] = []
    
    def json(self):
        return {
            'variables': {},
            'lists': {},
            'broadcasts': {},
            'blocks': {},
            'comments': {},
            'costumes': [costume.json() for costume in self.costumes],
            'sounds': [],
            'currentCostume': self.current_costume,
            'layerOrder': self.layer_order,
            'volume': self.volume
        }


class Sprite(Target):
    def json(self):
        target_json = super().json()
        target_json['isStage'] = False
        target_json['name'] = self.name
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
        
        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0])
        main_dir = os.path.dirname(os.path.abspath(caller_module.__file__))
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
