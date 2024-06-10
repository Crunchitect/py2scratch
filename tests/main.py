import sys
sys.path.insert(0, '..')
from src.scratch import Project, Stage, Sprite, Sound, Costume

proj = Project()

Stage = Stage()
Stage.costumes.append(Costume('crunchi', './assets/background.png'))
Stage.sounds.append(Sound('blitz', './assets/hyper-velocity.mp3'))

toilet = Sprite('skibidi')
toilet.costumes.append(Costume('toilet', './assets/toilet.svg'))

proj.add(Stage)
proj.add(toilet)
proj.build()