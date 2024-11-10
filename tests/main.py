import sys
sys.path.insert(0, '..')
from py2scratch.scratch import Project, Stage, Sprite, Sound, Costume, RotationStyles

proj = Project()

Stage = Stage()
Stage.costumes.append(Costume('crunchi', './assets/background.png'))
Stage.sounds.append(Sound('blitz', './assets/hyper-velocity.mp3'))

toilet = Sprite('skibidi')
toilet.rotation = 180
toilet.rotation_style = RotationStyles.LEFT_RIGHT
toilet.costumes.append(Costume('toilet', './assets/toilet.svg'))

def _flag_clicked(sprite):
    print(4)

toilet.funcs.append(_flag_clicked)

proj.add(Stage)
proj.add(toilet)
proj.build()