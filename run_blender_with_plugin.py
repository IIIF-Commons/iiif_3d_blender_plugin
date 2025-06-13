import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

import sys
import os
import bpy

# Ensure the script receives the correct number of arguments
if len(sys.argv) < 4:
    print(
        "Usage: blender --background --python run_blender_with_plugin.py -- <input_manifest>"
    )
    sys.exit(1)

# Get the input and output manifest file paths from the command line arguments
input_manifest = sys.argv[sys.argv.index("--") + 1]

context = bpy.context
if context is None:
    print("Failed to get the Blender context")
    sys.exit(1)


def get_extension_id():
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "blender_manifest.toml")
        with open(manifest_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("id = "):
                    # Extract the value between quotes
                    return line.split("=")[1].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Error reading blender_manifest.toml: {e}")
        sys.exit(1)
    print("Could not find id in blender_manifest.toml")
    sys.exit(1)


# Load the plugin
needle = get_extension_id()
logger.debug("needle is %s" % (needle,))
ext_name = None
logger.debug("addons.keys is %s" % ( "\n".join( context.preferences.addons.keys()),))
for key in context.preferences.addons.keys():
    if needle in key:
        ext_name = key
        logger.debug("ext_name is %s" % (ext_name,))
        break

if not ext_name:
    print("Failed to find the plugin")
    sys.exit(1)

bpy.ops.preferences.addon_enable(module=ext_name)



if ext_name not in context.preferences.addons:
    print("Failed to load the plugin")
    sys.exit(1)


try:
    bpy.ops.import_scene.iiif_manifest(filepath=input_manifest)
except Exception as exc:
    print(str(exc))
    sys.exit(1)
else:
    sys.exit(0)
