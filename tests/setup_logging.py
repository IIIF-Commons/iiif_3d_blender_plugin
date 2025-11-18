import logging
import sys

for hndlr in  logging.getLogger().handlers[:]:
    logging.getLogger().removeHandler(hndlr)
    
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger().warning("configured by tests/setup_logging.py")

# following is done to avoid double printing of glTF messages
# since glTF adds its own StreamHandlers to stdout and stderr
# see scripts/addons_core/io_scene_gltf2/io/com/debug.py
# and scripts/addons_core/io_scene_gltf2/__init__.py
# in https://projects.blender.org/blender/blender
glTF_logger = logging.getLogger("glTFImporter")
glTF_logger.propagate = False

def register():
    pass
