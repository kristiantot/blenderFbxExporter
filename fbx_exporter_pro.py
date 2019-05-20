
bl_info = {
    "name": "FBX Exporter Pro",
    "author": "Den Coda",
    "version": (1, 0, 0),
    "blender": (2, 7, 9),
    "location": "View3D > Tools > FBX Exporter Pro",
    "description": "Adds some tools for improve the blender to unity workflow",
    "warning": "",
    "wiki_url": "",
    "category": "FBX Exporter Pro"}

import os

import bpy

if "bpy" in locals():
    import importlib
    if "import_fbx" in locals():
        importlib.reload(import_fbx)
    if "export_fbx_bin" in locals():
        importlib.reload(export_fbx_bin)
    if "export_fbx" in locals():
        importlib.reload(export_fbx)
from bpy.types import Operator
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper_factory,
        path_reference_mode,
        axis_conversion,
        )
IOFBXOrientationHelper = orientation_helper_factory("IOFBXOrientationHelper", axis_forward='-Z', axis_up='Y')
class FBXExportSettings(PropertyGroup,IOFBXOrientationHelper):
    #Custom
    export_models= BoolProperty(
            name="Models",
            description="Export Selected Models",
            default=True,
            )

    export_animations= BoolProperty(
            name="Animations",
            description="Export  Animations",
            default=True,
            )
    export_scene = BoolProperty(
            name="Complete Scene",
            description="Export Compet Scene As One FBX File",
            default=False,
            )
    export_selected_only = BoolProperty(
            name="Selected Only",
            description="Export Selcted Only",
            default=False,
            )



    #---------------
    version = EnumProperty(
            items=(('BIN7400', "FBX 7.4 binary", "Modern 7.4 binary version"),
                   ('ASCII6100', "FBX 6.1 ASCII",
                                 "Legacy 6.1 ascii version - WARNING: Deprecated and no more maintained"),
                   ),
            name="Version",
            description="Choose which version of the exporter to use",
            )

    # 7.4 only
    ui_tab = EnumProperty(
            items=(('MAIN', "Main", "Main basic settings"),
                   ('GEOMETRY', "Geometries", "Geometry-related settings"),
                   ('ARMATURE', "Armatures", "Armature-related settings"),
                   ('ANIMATION', "Animation", "Animation-related settings"),
                   ),
            name="ui_tab",
            description="Export options categories",
            )

    use_selection = BoolProperty(
            name="Selected Objects",
            description="Export selected objects on visible layers",
            default=False,
            )
    global_scale = FloatProperty(
            name="Scale",
            description="Scale all data (Some importers do not support scaled armatures!)",
            min=0.001, max=1000.0,
            soft_min=0.01, soft_max=1000.0,
            default=1.0,
            )
    # 7.4 only
    apply_unit_scale = BoolProperty(
            name="Apply Unit",
            description="Take into account current Blender units settings (if unset, raw Blender Units values are used as-is)",
            default=True,
            )
    # 7.4 only
    apply_scale_options = EnumProperty(
            items=(('FBX_SCALE_NONE', "All Local",
                    "Apply custom scaling and units scaling to each object transformation, FBX scale remains at 1.0"),
                   ('FBX_SCALE_UNITS', "FBX Units Scale",
                    "Apply custom scaling to each object transformation, and units scaling to FBX scale"),
                   ('FBX_SCALE_CUSTOM', "FBX Custom Scale",
                    "Apply custom scaling to FBX scale, and units scaling to each object transformation"),
                   ('FBX_SCALE_ALL', "FBX All",
                    "Apply custom scaling and units scaling to FBX scale"),
                   ),
            name="Apply Scalings",
            description="How to apply custom and units scalings in generated FBX file "
                        "(Blender uses FBX scale to detect units on import, "
                        "but many other applications do not handle the same way)",

            )
    # 7.4 only
    bake_space_transform = BoolProperty(
            name="!EXPERIMENTAL! Apply Transform",
            description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
                        "target space is not aligned with Blender's space "
                        "(WARNING! experimental option, use at own risks, known broken with armatures/animations)",
            default=False,
            )

    object_types = EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                   ('CAMERA', "Camera", ""),
                   ('LAMP', "Lamp", ""),
                   ('ARMATURE', "Armature", "WARNING: not supported in dupli/group instances"),
                   ('MESH', "Mesh", ""),
                   ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
                   ),
            description="Which kind of object to export",
            default={'EMPTY', 'ARMATURE', 'MESH', 'OTHER'},
            )

    use_mesh_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers to mesh objects (except Armature ones) - "
                        "WARNING: prevents exporting shape keys",
            default=True,
            )
    use_mesh_modifiers_render = BoolProperty(
            name="Use Modifiers Render Setting",
            description="Use render settings when applying modifiers to mesh objects",
            default=True,
            )
    mesh_smooth_type = EnumProperty(
            name="Smoothing",
            items=(('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            description="Export smoothing information "
                        "(prefer 'Normals Only' option if your target importer understand split normals)",
            default='OFF',
            )
    use_mesh_edges = BoolProperty(
            name="Loose Edges",
            description="Export loose edges (as two-vertices polygons)",
            default=False,
            )
    # 7.4 only
    use_tspace = BoolProperty(
            name="Tangent Space",
            description="Add binormal and tangent vectors, together with normal they form the tangent space "
                        "(will only work correctly with tris/quads only meshes!)",
            default=False,
            )
    # 7.4 only
    use_custom_props = BoolProperty(
            name="Custom Properties",
            description="Export custom properties",
            default=False,
            )
    add_leaf_bones = BoolProperty(
            name="Add Leaf Bones",
            description="Append a final bone to the end of each chain to specify last bone length "
                        "(use this when you intend to edit the armature from exported data)",
            default=True # False for commit!
            )
    primary_bone_axis = EnumProperty(
            name="Primary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='Y',
            )
    secondary_bone_axis = EnumProperty(
            name="Secondary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='X',
            )
    use_armature_deform_only = BoolProperty(
            name="Only Deform Bones",
            description="Only write deforming bones (and non-deforming ones when they have deforming children)",
            default=False,
            )
    armature_nodetype = EnumProperty(
            name="Armature FBXNode Type",
            items=(('NULL', "Null", "'Null' FBX node, similar to Blender's Empty (default)"),
                   ('ROOT', "Root", "'Root' FBX node, supposed to be the root of chains of bones..."),
                   ('LIMBNODE', "LimbNode", "'LimbNode' FBX node, a regular joint between two bones..."),
                  ),
            description="FBX type of node (object) used to represent Blender's armatures "
                        "(use Null one unless you experience issues with other app, other choices may no import back "
                        "perfectly in Blender...)",
            default='NULL',
            )
    # Anim - 7.4
    bake_anim = BoolProperty(
            name="Baked Animation",
            description="Export baked keyframe animation",
            default=True,
            )
    bake_anim_use_all_bones = BoolProperty(
            name="Key All Bones",
            description="Force exporting at least one key of animation for all bones "
                        "(needed with some target applications, like UE4)",
            default=True,
            )
    bake_anim_use_nla_strips = BoolProperty(
            name="NLA Strips",
            description="Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
                        "instead of global scene animation",
            default=False,
            )
    bake_anim_use_all_actions = BoolProperty(
            name="All Actions",
            description="Export each action as a separated FBX's AnimStack, instead of global scene animation "
                        "(note that animated objects will get all actions compatible with them, "
                        "others will get no animation at all)",
            default=True,
            )
    bake_anim_force_startend_keying = BoolProperty(
            name="Force Start/End Keying",
            description="Always add a keyframe at start and end of actions for animated channels",
            default=True,
            )
    bake_anim_step = FloatProperty(
            name="Sampling Rate",
            description="How often to evaluate animated values (in frames)",
            min=0.01, max=100.0,
            soft_min=0.1, soft_max=10.0,
            default=1.0,
            )
    bake_anim_simplify_factor = FloatProperty(
            name="Simplify",
            description="How much to simplify baked values (0.0 to disable, the higher the more simplified)",
            min=0.0, max=100.0,  # No simplification to up to 10% of current magnitude tolerance.
            soft_min=0.0, soft_max=10.0,
            default=1.0,  # default: min slope: 0.005, max frame step: 10.
            )
    # Anim - 6.1
    use_anim = BoolProperty(
            name="Animation",
            description="Export keyframe animation",
            default=True,
            )
    use_anim_action_all = BoolProperty(
            name="All Actions",
            description=("Export all actions for armatures or just the currently selected action"),
            default=True,
            )
    use_default_take = BoolProperty(
            name="Default Take",
            description="Export currently assigned object and armature animations into a default take from the scene "
                        "start/end frames",
            default=True
            )
    use_anim_optimize = BoolProperty(
            name="Optimize Keyframes",
            description="Remove double keyframes",
            default=True,
            )
    anim_optimize_precision = FloatProperty(
            name="Precision",
            description="Tolerance for comparing double keyframes (higher for greater accuracy)",
            min=0.0, max=20.0,  # from 10^2 to 10^-18 frames precision.
            soft_min=1.0, soft_max=16.0,
            default=6.0,  # default: 10^-4 frames.
            )
    # End anim
    path_mode = path_reference_mode
    # 7.4 only
    embed_textures = BoolProperty(
            name="Embed Textures",
            description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
            default=False,
            )
    batch_mode = EnumProperty(
            name="Batch Mode",
            items=(('OFF', "Off", "Active scene to file"),
                   ('SCENE', "Scene", "Each scene as a file"),
                   ('GROUP', "Group", "Each group as a file"),
                   ),
            )
    use_batch_own_dir = BoolProperty(
            name="Batch Own Dir",
            description="Create a dir for each exported file",
            default=True,
            )
    use_metadata = BoolProperty(
            name="Use Metadata",
            default=True,
            options={'HIDDEN'},
            )
    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        from mathutils import Matrix
        if not self.filepath:
            raise Exception("filepath not set")

        global_matrix = (axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())

        keywords = self.as_keywords(ignore=("check_existing",
                                            "filter_glob",
                                            "ui_tab",
                                            ))

        keywords["global_matrix"] = global_matrix

        if self.version == 'BIN7400':
            from . import export_fbx_bin
            return export_fbx_bin.save(self, context, **keywords)
        else:
            from . import export_fbx
            return export_fbx.save(self, context, **keywords)

class FBXExporterPro(bpy.types.Panel):

    """Creates a Panel in the Object properties window"""
    bl_label = "FBX Exporter Pro"
    bl_idname = "OBJECT_PT_swgtools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "FBX Exporter Pro"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        fbxsettings = scene.fbx_settings

        obj = context.object

        col = layout.column()
        col.prop(context.scene, 'conf_path')
        row = layout.row()
        row.scale_y =2
        row.operator("button.export_animations", text='Export')
        row = layout.row()
        row.prop(fbxsettings, "export_models")
        row = layout.row()
        row.prop(fbxsettings, "export_animations")
        row = layout.row()
        row.prop(fbxsettings, "export_scene")
        row = layout.row()

        row.label(text="")
        row = layout.row()
        row.prop(fbxsettings, "export_selected_only")
        row = layout.row()
        row.label(text="All Animation Actions:")
        ob = context.object
        layout.template_list("ACTION_UL_list", "", bpy.data, "actions", ob, "action_list_index")
        row = layout.row()
        #layout.template_list("SELECTED_ACTION_UL_list", "", bpy.data, "materials", ob, "selected_action_list_index")
        row = layout.row()

        row.label(text="FBX Export Properties:")

        layout.prop(fbxsettings, "version")

        if fbxsettings.version == 'BIN7400':
            layout.prop(fbxsettings, "ui_tab", expand=True)
            if fbxsettings.ui_tab == 'MAIN':
                #layout.prop(fbxsettings, "use_selection")

                layout.prop(fbxsettings, "axis_forward")
                layout.prop(fbxsettings, "axis_up")
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(fbxsettings, "global_scale")
                sub = row.row(align=True)
                sub.prop(fbxsettings, "apply_unit_scale", text="", icon='NDOF_TRANS')
                col.prop(fbxsettings, "apply_scale_options")

                layout.prop(fbxsettings, "axis_forward")
                layout.prop(fbxsettings, "axis_up")

                layout.separator()
                layout.prop(fbxsettings, "object_types")
                layout.prop(fbxsettings, "bake_space_transform")
                layout.prop(fbxsettings, "use_custom_props")

                layout.separator()
                row = layout.row(align=True)
                row.prop(fbxsettings, "path_mode")
                sub = row.row(align=True)
                sub.enabled = (fbxsettings.path_mode == 'COPY')
                sub.prop(fbxsettings, "embed_textures", text="", icon='PACKAGE' if fbxsettings.embed_textures else 'UGLYPACKAGE')
                row = layout.row(align=True)
                row.prop(fbxsettings, "batch_mode")
                sub = row.row(align=True)
                sub.prop(fbxsettings, "use_batch_own_dir", text="", icon='NEWFOLDER')
            elif fbxsettings.ui_tab == 'GEOMETRY':
                layout.prop(fbxsettings, "use_mesh_modifiers")
                sub = layout.row()
                sub.enabled = fbxsettings.use_mesh_modifiers
                sub.prop(fbxsettings, "use_mesh_modifiers_render")
                layout.prop(fbxsettings, "mesh_smooth_type")
                layout.prop(fbxsettings, "use_mesh_edges")
                sub = layout.row()
                #~ sub.enabled = self.mesh_smooth_type in {'OFF'}
                sub.prop(fbxsettings, "use_tspace")
            elif fbxsettings.ui_tab == 'ARMATURE':
                layout.prop(fbxsettings, "use_armature_deform_only")
                layout.prop(fbxsettings, "add_leaf_bones")
                layout.prop(fbxsettings, "primary_bone_axis")
                layout.prop(fbxsettings, "secondary_bone_axis")
                layout.prop(fbxsettings, "armature_nodetype")
            elif fbxsettings.ui_tab == 'ANIMATION':
                layout.prop(fbxsettings, "bake_anim")
                col = layout.column()
                col.enabled = fbxsettings.bake_anim
                col.prop(fbxsettings, "bake_anim_use_all_bones")
                col.prop(fbxsettings, "bake_anim_use_nla_strips")
                #col.prop(fbxsettings, "bake_anim_use_all_actions")
                col.prop(fbxsettings, "bake_anim_force_startend_keying")
                col.prop(fbxsettings, "bake_anim_step")
                col.prop(fbxsettings, "bake_anim_simplify_factor")
        else:
            layout.prop(fbxsettings, "use_selection")
            layout.prop(fbxsettings, "global_scale")
            layout.prop(fbxsettings, "axis_forward")
            layout.prop(fbxsettings, "axis_up")

            layout.separator()
            layout.prop(fbxsettings, "object_types")
            layout.prop(fbxsettings, "use_mesh_modifiers")
            layout.prop(fbxsettings, "mesh_smooth_type")
            layout.prop(fbxsettings, "use_mesh_edges")
            sub = layout.row()
            #~ sub.enabled = self.mesh_smooth_type in {'OFF'}
            sub.prop(fbxsettings, "use_tspace")
            layout.prop(fbxsettings, "use_armature_deform_only")
            layout.prop(fbxsettings, "use_anim")
            col = layout.column()
            col.enabled = fbxsettings.use_anim
            col.prop(fbxsettings, "use_anim_action_all")
            col.prop(fbxsettings, "use_default_take")
            col.prop(fbxsettings, "use_anim_optimize")
            col.prop(fbxsettings, "anim_optimize_precision")

            layout.separator()
            layout.prop(fbxsettings, "path_mode")

            layout.prop(fbxsettings, "batch_mode")
            layout.prop(fbxsettings, "use_batch_own_dir")



class fbxProperties(bpy.types.Operator):
            bl_idname = "object.fbxproperties_operator"
            bl_label = "FBX Properties"


            globalScale = bpy.props.FloatProperty(
            name="global_scale",
            default=1.0,
            description="Global Scale"
            )

class buttonExportAnimations(bpy.types.Operator):

    bl_idname = "button.export_animations"
    bl_label = "Export Animations"


    def execute(self, context):
        fbxsettings = context.scene.fbx_settings
        blend_filename = bpy.path.basename(bpy.context.blend_data.filepath)
        filename = blend_filename.replace('.blend', '')
        rootPath = '{0}{1}'.format(filename,"_Blender_Export/")
        selectedPath ='{0}{1}'.format(bpy.path.abspath(bpy.context.scene.conf_path),rootPath)



        #MODELS PATH
        if fbxsettings.export_models:
           modelsFolderName = 'Models/'
           modelsFolderPath = (selectedPath+modelsFolderName)

           if not os.path.exists(modelsFolderPath):
            m = '{0}{1}'.format(selectedPath,modelsFolderName)
            modelsFolderPath = os.makedirs(m)
        #ANIMS PATH
        if fbxsettings.export_animations:
           animsFolderName = 'Animations/'
           animsFolderPath = (selectedPath+animsFolderName)

           if not os.path.exists(animsFolderPath):
            a = '{0}{1}'.format(selectedPath,animsFolderName)
            animsFolderPath = os.makedirs(a)

        #SCENE PATH
        if fbxsettings.export_scene:
           sceneFolderName = 'Scene/'
           sceneFolderPath = (selectedPath+sceneFolderName)

           if not os.path.exists(sceneFolderPath):
            s = '{0}{1}'.format(selectedPath,sceneFolderName)
            sceneFolderPath = os.makedirs(s)



        if fbxsettings.export_animations:
            fullPath = "{0}{1}".format(selectedPath,animsFolderName)
            type = {'ARMATURE'}
            first_frame = 9999
            last_frame = -9999
            scn = bpy.context.scene
            if fbxsettings.export_selected_only:
                ob = bpy.context.object

                act = bpy.data.actions[ob.action_list_index]
                if  act.frame_range[1] > last_frame :
                    scn.frame_end = act.frame_range[1]
                if act.frame_range[0] < first_frame :
                    scn.frame_start = act.frame_range[0]
                filename = "{0}_{1}".format(bpy.context.object.name, act.name)
                path = "{0}@{1}.fbx".format(fullPath, filename)
                Export(path,True,False,False,type)


            else:
                act = bpy.data.actions
                l = []
                c = len(act)

                for a in act:

                    if bpy.context.object.type != 'ARMATURE':
                        self.report({'INFO'}, 'Armature with animations must be selected')
                        continue
                    l.append(a)

                    bpy.context.object.animation_data.action = a
                    if  a.frame_range[1] > last_frame :
                        scn.frame_end = a.frame_range[1]
                    if a.frame_range[0] < first_frame :
                        scn.frame_start = a.frame_range[0]
                    filename = "{0}_{1}".format(bpy.context.object.name, a.name)
                    path = "{0}@{1}.fbx".format(fullPath, filename)
                    Export(path,True,False,False,type)


        if fbxsettings.export_models:
            fullPath = "{0}{1}".format(selectedPath,modelsFolderName)
            scene = bpy.context.scene

            if bpy.ops.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode = 'OBJECT')

            type = {'MESH','ARMATURE'}

            if fbxsettings.export_selected_only:
                selected_objects = [ o for o in bpy.context.scene.objects if o.select ]
                obj = selected_objects
            else:
                obj = scene.objects

            lo = []
            co = len(obj)

            for o in obj:

                lo.append(o)


                filename = o.name
                path = "{0}{1}.fbx".format(fullPath, filename)
                Export(path,False,True,False,type)



        if fbxsettings.export_scene:
            fullPath = "{0}{1}".format(selectedPath,sceneFolderName)
            scene = bpy.context.scene

            if bpy.ops.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode = 'OBJECT')

            type = {'EMPTY', 'CAMERA', 'LAMP', 'ARMATURE', 'MESH', 'OTHER'}

            blend_filename = bpy.path.basename(bpy.context.blend_data.filepath)
            filename = blend_filename.replace(".blend", "")+"_Scene"

            path = "{0}{1}.fbx".format(fullPath, filename)
            Export(path,False,True,True,type)
        return {'FINISHED'}



def Export(path = "",isExportAnimations = True, isExportModels = True, isExportScene = False,type = {''}):


    fbxsettings = bpy.context.scene.fbx_settings

    bpy.ops.export_scene.fbx(filepath=path,
                                     check_existing=True,
                                     axis_forward=fbxsettings.axis_forward,
                                     axis_up=fbxsettings.axis_up,
                                     filter_glob="*.fbx",
                                     #commented not used in 2.8
                                     #version='BIN7400',
                                     ui_tab='MAIN',
                                     use_selection=fbxsettings.export_selected_only,
                                     global_scale=fbxsettings.global_scale,
                                     apply_unit_scale=fbxsettings.apply_unit_scale,
                                     apply_scale_options = fbxsettings.apply_scale_options,
                                     bake_space_transform=fbxsettings.bake_space_transform,
                                     object_types=type,
                                     bake_anim=isExportAnimations,
                                     use_mesh_modifiers=True,
                                     mesh_smooth_type='OFF',
                                     use_mesh_edges=False,
                                     use_tspace=False,
                                     use_custom_props=False,
                                     add_leaf_bones=True,
                                     primary_bone_axis='Y',
                                     secondary_bone_axis='X',
                                     use_armature_deform_only=False,
                                     armature_nodetype='NULL',
                                     bake_anim_use_all_bones=True,
                                     bake_anim_use_nla_strips=False,
                                     bake_anim_use_all_actions=False,
                                     bake_anim_force_startend_keying=True,
                                     bake_anim_step=1.0,
                                     bake_anim_simplify_factor=1.0,
                                     #use_anim=True,
                                     #use_anim_action_all=True,
                                    # use_default_take=True,
                                    # use_anim_optimize=True,
                                    # anim_optimize_precision=6.0,
                                     path_mode='AUTO',
                                     embed_textures=False,
                                     batch_mode='OFF',
                                     use_batch_own_dir=True,
                                     use_metadata=True)
                                     # bpy.ops.export_scene.fbx(filepath="",
                                     #  check_existing=True,
                                     #   filter_glob="*.fbx",
                                     #    ui_tab='MAIN',
                                     #     use_selection=False,
                                     #      use_active_collection=False,
                                     #       global_scale=1.0,
                                     #        apply_unit_scale=True,
                                     #         apply_scale_options='FBX_SCALE_NONE',
                                     #          bake_space_transform=False,
                                     #           object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'},
                                     #            use_mesh_modifiers=True,
                                     #             use_mesh_modifiers_render=True,
                                     #             mesh_smooth_type='OFF',
                                     #              use_mesh_edges=False,
                                     #               use_tspace=False,
                                     #                use_custom_props=False,
                                     #                 add_leaf_bones=True,
                                     #                  primary_bone_axis='Y',
                                     #                  secondary_bone_axis='X',
                                     #                   use_armature_deform_only=False,
                                     #                    armature_nodetype='NULL',
                                     #                     bake_anim=True,
                                     #                      bake_anim_use_all_bones=True,
                                     #                       bake_anim_use_nla_strips=True,
                                     #                        bake_anim_use_all_actions=True,
                                     #                         bake_anim_force_startend_keying=True,
                                     #                          bake_anim_step=1.0,
                                     #                           bake_anim_simplify_factor=1.0,
                                     #                           path_mode='AUTO',
                                     #                           embed_textures=False,
                                     #                            batch_mode='OFF',
                                     #                            use_batch_own_dir=True,
                                     #                            use_metadata=True,
                                     #                             axis_forward='-Z',
                                     #                              axis_up='Y')

def action_editor_update(context):

    ob = bpy.context.object


    ad = ob.animation_data
    if ad == None:

        return{'FINISHED'}
    if ad:
        if not ad.action:

            return{'FINISHED'}
        else:

            action_index = bpy.data.actions.find(ob.animation_data.action.name)
            if action_index != ob.action_list_index:
                ob.action_list_index = action_index


bpy.app.handlers.scene_update_post.append(action_editor_update)


def update_action_list(self, context):
    ob = bpy.context.object

    ob.animation_data.action = bpy.data.actions[ob.action_list_index]
    bpy.context.scene.frame_current = 1


class ACTION_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass

def register():
    bpy.types.Object.action_list_index = bpy.props.IntProperty(update=update_action_list)
    bpy.utils.register_class(FBXExporterPro)
    bpy.utils.register_class(fbxProperties)
    bpy.utils.register_class(buttonExportAnimations)
    bpy.utils.register_module(__name__)
    bpy.types.Scene.fbx_settings = PointerProperty(type=FBXExportSettings)


    bpy.types.Scene.conf_path = bpy.props.StringProperty(
        name="Path",
        default="",
        description="Define the export Folder, Sub Folders Will Be Created",
        subtype='DIR_PATH'
    )


def unregister():
    bpy.utils.unregister_class(FBXExporterPro)
    bpy.utils.unregister_class(fbxProperties)
    bpy.utils.unregister_class(buttonExportAnimations)
    del bpy.types.Scene.conf_path
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.fbx_settings
    del bpy.types.Object.action_list_index


if __name__ == "__main__":
    register()
