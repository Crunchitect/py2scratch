from src.scratch import Project, Stage, Sprite, Costume

proj = Project()

Stage = Stage()
Stage.costumes.append(Costume('crunchi', './assets/background.png'))

toilet = Sprite('skibidi')
toilet.costumes.append(Costume('toilet', './assets/toilet.svg'))

proj.add(Stage)
proj.add(toilet)
proj.build()