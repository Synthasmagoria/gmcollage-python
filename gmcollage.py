import xml.etree.ElementTree as ET
import sys
import os.path
import json
import shutil

class ModulePart:
    module_resources_iterator = None
    def __init__(self, _module_name, _module_path, _resource_type, _resource_path):
        self.module_name = _module_name
        self.module_path = _module_path
        self.resource_type = _resource_type
        self.resource_path = _resource_path

RESOURCE_TYPES = ["datafiles", "sounds", "sprites", "backgrounds", "paths", "scripts", "shaders", "fonts", "objects", "timelines", "rooms"]
RESOURCE_PATHS = {
    "datafiles": "datafiles",
    "sounds": "sound",
    "sprites": "sprites",
    "backgrounds": "background",
    "paths": "paths",
    "scripts": "scripts",
    "shaders": "shaders",
    "fonts": "fonts",
    "objects": "objects",
    "timelines": "timelines",
    "rooms": "rooms"
}
RESOURCE_TAG_NAMES = {
    "datafiles": "datafile",
    "sounds": "sound",
    "sprites": "sprite",
    "backgrounds": "background",
    "paths": "path",
    "scripts": "script",
    "shaders": "shader",
    "fonts": "font",
    "objects": "object",
    "timelines": "timeline",
    "rooms": "room"
}
RESOURCE_FILE_EXTENSIONS = {
    "datafiles": "",
    "sounds": ".sound.gmx",
    "sprites": ".sprite.gmx",
    "backgrounds": ".background.gmx",
    "paths": ".path.gmx",
    "scripts": "",
    "shaders": "",
    "fonts": ".font.gmx",
    "objects": ".object.gmx",
    "timelines": ".timeline.gmx",
    "rooms": ".room.gmx"
}

argument_number = len(sys.argv)
error_state = False

if argument_number < 2:
    print("""################## GMCOLLAGE ##################
Usage: py gmcollage.py <project.gmx> in/out <module folder/.moduleconfig> <OPTIONAL SWITCHES>
Providing multiple module/moduleconfig paths can be done with using spaces
-o <DIR>    | Module output directory (OUT only)
-t          | Run checks only (no copying files or modifying project file)

The .moduleconfig format used in \"out\" mode is a json list containing the name of the resource type, and resource folder path:
[
    ["sprites", "Synthas"],
    ["backgrounds", "big/folder/with/backgrounds"]
    ["timelines", "Synthas"],
    ["objects", "Synthas"],
    ["rooms", "Synthas"]
]
""")
    sys.exit()

gmx_path = sys.argv[1].replace("\\", "/")
if not os.path.isfile(gmx_path):
    error_state = True
    print("Error: Project file path does not point to a file")

if argument_number < 3:
    sys.exit("Error: Missing program mode argument (in/out)")
else:
    program_mode = sys.argv[2]
    if program_mode != "out" and program_mode != "in":
        error_state = True
        print("Error: invalid program mode (in/out)")

if argument_number < 4:
    error_state = True
    if program_mode == "out":
        print("Error: no moduleconfigs were passed")
    elif program_mode == "in":
        print("Error: no modules were passed")
    else:
        print("Error: No moduleconfigs or modules were passed")

argument_index = 3
paths = []
module_output_directory = "modules"
test_mode = False
while argument_index < argument_number:
    arg = sys.argv[argument_index]
    if len(arg) == 0:
        error_state = True
        print("Error: Empty string is an invalid argument")
        break
    if len(arg) > 1 and arg[0] == '-':
        match arg[1]:
            case 'o':
                # TODO: Make possible to set directory in 'in' mode
                argument_index += 1
                if argument_index >= argument_number:
                    error_state = True
                    print("Error: '-o' switch passed but no accompanying argument")
                else:
                    module_output_directory = sys.argv[argument_index]
                    if not os.path.isdir(module_output_directory):
                        print("Log: Created module output directory at", module_output_directory)
                        os.makedirs(module_output_directory)
            case 't':
                if test_mode:
                    print("Error: No need to pass test flag \"-t\" more than once")
                    sys.exit()
                test_mode = True
            case 'c':
                pass # TODO: copy resources from module directory instead of moving ("in-only")
            case 'l':
                pass # TODO: leave folders empty instead of taking them out entirely
        if error_state:
            break
    else:
        if program_mode == "out" and not os.path.isfile(arg):
            error_state = True
            print("Error: Argument", argument_index, "does not point to a file")
        elif program_mode == "in" and not os.path.isdir(arg):
            error_state = True
            print("Error: Argument", argument_index, "does not point to a directory")
        else:
            paths.append(arg)
    
    argument_index += 1

gmx_directory = "".join(gmx_path.split("/")[:-1]) + "/"

def gmcollage_out():
    moduleconfig_paths = paths
    moduleconfig_number = len(moduleconfig_paths)
    moduleconfig_names = [name.split(".")[0] for name in moduleconfig_paths]
    moduleconfig_parts_grouped = [[]] * moduleconfig_number
    moduleconfig_parts = []

    for name in moduleconfig_names:
        for key, value in RESOURCE_PATHS.items():
            if not os.path.exists(module_output_directory + "/" + name + "/" + value):
                os.makedirs(module_output_directory + "/" + name + "/" + value)

    module_trees = [None] * moduleconfig_number
    module_roots = [None] * moduleconfig_number
    for i in range(moduleconfig_number):
        module_trees[i] = ET.ElementTree(ET.Element("module"))
        module_roots[i] = module_trees[i].getroot()

    for i in range(moduleconfig_number):
        with open(moduleconfig_paths[i], "r") as moduleconfig_file:
            try:
                moduleconfig_data = json.load(moduleconfig_file)
            except Exception as e:
                sys.exit("Error: JSON parser exception: " + str(e))
            for moduleconfig_pair in moduleconfig_data:
                part = ModulePart(moduleconfig_names[i], moduleconfig_paths[i].replace("\\", "/"), moduleconfig_pair[0], moduleconfig_pair[1].replace("\\", "/"))
                moduleconfig_parts_grouped[i].append(part)
                moduleconfig_parts.append(part)

    module_part_duplicates = []
    module_part_nested = []
    module_part_invalid_resource_type = []
    for mp_a in moduleconfig_parts:
        if not mp_a.resource_type in RESOURCE_TYPES:
            module_part_invalid_resource_type.append(mp_a)
        for mp_b in moduleconfig_parts:
            if mp_a == mp_b:
                continue
            if (mp_a.resource_path == mp_b.resource_path and mp_a.resource_type == mp_b.resource_type and
                not [mp_a, mp_b] in module_part_duplicates and not [mp_b, mp_a] in module_part_duplicates):
                    module_part_duplicates.append([mp_a, mp_b])
            if mp_a.resource_type == mp_b.resource_type:
                a = mp_a.resource_path.rstrip('/')
                b = mp_b.resource_path.rstrip('/')
                if (a.find(b) == 0 and len(a) > len(b) and a[len(b)] == '/'):
                    module_part_nested.append([mp_a, mp_b])

    error_state = False

    if len(module_part_duplicates) > 0:
        print("Error: Found duplicate paths in parts of modules")
        error_state = True
        for mp_dup in module_part_duplicates:
            if mp_dup[0].module_path == mp_dup[1].module_path:
                print(mp_dup[0].module_path, "pointed to", "\"" + mp_dup[0].resource_type + "," + mp_dup[0].resource_path + "\"", "twice")
            else:
                print(mp_dup[0].module_path, "and", mp_dup[1].module_path, "both pointed to", "\"" + mp_dup[0].resource_type + "," + mp_dup[0].resource_path + "\"")

    if len(module_part_nested) > 0:
        print("Error: Found nested resource paths in modules")
        error_state = True
        for mp_nest in module_part_nested:
            a = "\"" + mp_nest[0].resource_type + "," + mp_nest[0].resource_path + "\""
            b = "\"" + mp_nest[1].resource_type + "," + mp_nest[1].resource_path + "\""
            if mp_nest[0].module_path == mp_nest[1].module_path:
                print(mp_nest[0].module_path, "pointed to", a, "which is nested in", b)
            else:
                print(mp_nest[0].module_path, "pointed to", a, "and", mp_nest[1].module_path, "pointed to", b, "which is nested")

    if len(module_part_invalid_resource_type) > 0:
        print("Error: Found invalid resource types in modules")
        error_state = True
        for mp_inv_rtype in module_part_invalid_resource_type:
            print(mp_inv_rtype.module_path, "was pointing to invalid resource type in", mp_inv_rtype.resource_type + "," + mp_inv_rtype.resource_path)

    if error_state:
        sys.exit()

    gmx_tree = ET.parse(gmx_path)
    gmx_root = gmx_tree.getroot()
    gmx_parents = {c: p for p in gmx_tree.iter() for c in p}
    module_parts_missing = []

    for i in range(moduleconfig_number):
        for mp in moduleconfig_parts_grouped[i]:
            xpath = mp.resource_type
            for folder_name in mp.resource_path.split("/"):
                xpath += "/" + mp.resource_type + "[@name='" + folder_name + "']"
            folder = gmx_root.find(xpath)
            if folder == None:
                module_parts_missing.append(mp)
                continue
            resources = folder.iter(RESOURCE_TAG_NAMES[mp.resource_type])
            if resources == None:
                print("Warning: Empty module folder '" + mp.resource_type + "/" + mp.resource_path + "'", "in", mp.module_path)
            mp.module_resources_iterator = resources

            module_part = ET.Element("part")
            module_part.set("resource_type", mp.resource_type)
            module_part.set("resource_path", mp.resource_path)
            module_part.append(folder)
            module_roots[i].append(module_part)

            folder_parent = gmx_parents[folder]
            folder_parent.remove(folder)

    if len(module_parts_missing) > 0:
        error_state = True
        for mp_missing in module_parts_missing:
            print("Error: Missing resource path in module, couldn't find '" + mp_missing.resource_type + "/" + mp_missing.resource_path + "'", "in", mp_missing.module_path)

    if error_state:
        sys.exit()

    if test_mode:
        return

    for i in range(moduleconfig_number):
        for mp in moduleconfig_parts_grouped[i]:
            for resource_tag in mp.module_resources_iterator:
                resource_src = gmx_directory + resource_tag.text + RESOURCE_FILE_EXTENSIONS[mp.resource_type]
                resource_dest = module_output_directory + "/" + moduleconfig_names[i] + "/" + resource_tag.text + RESOURCE_FILE_EXTENSIONS[mp.resource_type]
                shutil.move(resource_src, resource_dest)

    for i in range(moduleconfig_number):
        module_trees[i].write(module_output_directory + "/" + moduleconfig_names[i] + "/module")
    gmx_tree.write(gmx_path)

def gmcollage_in():
    module_dirs = paths
    module_paths = [directory + "/module" for directory in module_dirs]
    module_names = [directory.split("/")[-1] for directory in module_dirs]
    module_trees = [ET.parse(module_path) for module_path in module_paths]

    gmx_tree = ET.parse(gmx_path)
    gmx_root = gmx_tree.getroot()
    for resource_type in RESOURCE_TYPES:
        if resource_type == "datafiles":
            continue
        if gmx_root.find(resource_type) == None:
            ET.SubElement(gmx_root, resource_type)
    
    gmx_resources = []
    module_resources = []
    for key, name in RESOURCE_TAG_NAMES.items():
        if name == "datafile":
            continue
        for resource in gmx_tree.iter(name):
            gmx_resources.append(resource.text)
        for module_tree in module_trees:
            for resource in module_tree.iter(name):
                module_resources.append({"text": resource.text, "module_name": module_names[0]})

    error_state = False

    for resource in module_resources:
        if resource["text"] in gmx_resources:
            error_state = True
            print("Error: Resource", resource["text"], "exists in project and in module '" + resource["module_name"] + "'")
    
    if error_state:
        print("Rename the resource(s) in the project and try again")
        sys.exit()

    for module_tree in module_trees:
        for part in module_tree.iter("part"):
            gmx_resource_folder = gmx_root.find(part.get("resource_type"))
            resource_parent_path_parts = part.get("resource_path").split("/")[:-1]
            resource_parent_path = "/".join(resource_parent_path_parts)
            
            if resource_parent_path == "":
                gmx_resource_folder.append(part.find("*"))
                continue
            
            for resource_parent_path_part in resource_parent_path_parts:
                gmx_resource_subfolder = gmx_resource_folder.find(part.get("resource_type") + "[@name='" + resource_parent_path_part + "']")
                if gmx_resource_subfolder == None:
                    gmx_resource_subfolder = ET.SubElement(gmx_resource_folder, part.get("resource_type"))
                    gmx_resource_subfolder.set("name", resource_parent_path_part)
                gmx_resource_folder = gmx_resource_subfolder

            gmx_resource_folder.append(part.find("*"))

    if error_state:
        sys.exit()

    if test_mode:
        return

    for key, resource_path in RESOURCE_PATHS.items():
        for filename in os.listdir(module_dirs[0] + "/" + resource_path):
            resource_src = module_dirs[0] + "/" + resource_path + "/" + filename
            resource_dest = gmx_directory + "/" + resource_path + "/" + filename
            shutil.move(resource_src, resource_dest)

    gmx_tree.write(gmx_path)

if program_mode == "out":
    gmcollage_out()
    if not test_mode:
        print("Log: Successfully took out modules", str(paths))
elif program_mode == "in":
    gmcollage_in()
    if not test_mode:
        print("Log: Successfully put in", str(paths))

if test_mode:
    print("Log: Test mode finished without errors")