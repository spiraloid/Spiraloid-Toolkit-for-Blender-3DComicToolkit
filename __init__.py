bl_info = {
        'name': '3D Comic Toolkit',
        'author': 'bay raitt',
        'version': (0, 1),
        'blender': (2, 80, 0),
        'category': 'All',
        'location': 'Spiraloid > 3D Comic',
        'wiki_url': ''
}

modulesNames = ['3DComicToolkit']

modulesFullNames = []
for currentModuleName in modulesNames:
        modulesFullNames.append('{}.{}'.format(__name__, currentModuleName))

import sys
import importlib

for currentModuleFullName in modulesFullNames:
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)

# addCubeModule = sys.modules[modulesNames['addCubeClass']]



def register():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()

def unregister():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()

if __name__ == "__main__":
    register()