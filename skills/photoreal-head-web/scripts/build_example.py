"""Build the licensed Lee Perry-Smith head demonstration in background Blender.

Requires Blender >=4.2 and the original scan, two textures and attribution file.
Writes only a new/empty output directory; never changes source or shipped assets.
This recreates the demonstration, not a general head sculpting/release pipeline.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
INPUT_FILES = ('LeePerrySmith.glb', 'Map-COL.jpg',
               'Infinite-Level_02_Tangent_SmoothUV.jpg', 'LeePerrySmith_License.txt')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True, help='Directory containing the four original inputs')
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--resolution', type=int, default=800, help='Render width; height is width * 9/8')
    parser.add_argument('--samples', type=int, default=24)
    parser.add_argument('--skip-renders', action='store_true', help='Export model and editable project only')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    source, out = args.source_dir.expanduser().resolve(), args.out_dir.expanduser().resolve()
    if not source.is_dir() or any(not (source / name).is_file() for name in INPUT_FILES):
        parser.error('--source-dir must contain: ' + ', '.join(INPUT_FILES))
    if source.is_relative_to(out) or out.is_relative_to(source):
        parser.error('Input and output directories must not overlap')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error('--out-dir must be a new or empty directory')
    if not 64 <= args.resolution <= 4096 or not 1 <= args.samples <= 4096:
        parser.error('Use resolution 64..4096 and samples 1..4096')
    if any(not (source / name).resolve().is_relative_to(source) for name in INPUT_FILES):
        parser.error('Input symlinks must not escape the source directory')
    try:
        license_bytes = (source / INPUT_FILES[-1]).read_bytes()
        license_text = license_bytes.decode('utf-8-sig')
    except (OSError, UnicodeError) as exc:
        parser.error(f'Cannot read source attribution: {exc}')
    if not license_text.strip():
        parser.error('Source attribution must not be empty')
    return parser, args, source, out, license_bytes


def build(args, source, out, license_bytes):
    import bmesh
    import bpy
    from mathutils import Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source / 'LeePerrySmith.glb'))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        raise ValueError('Source GLB contains no meshes')
    coords = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector([min(v[i] for v in coords) for i in range(3)])
    high = Vector([max(v[i] for v in coords) for i in range(3)])
    if high.z - low.z <= 1e-8:
        raise ValueError('Source mesh has zero height')
    center, factor = (low + high) / 2, .28 / (high.z - low.z)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        matrix = obj.matrix_world.copy()
        for vertex in obj.data.vertices:
            vertex.co = (matrix @ vertex.co - center) * factor
        obj.matrix_world.identity()
        obj.name, obj.data.name = 'Head_Scan', 'Head_Scan_UV0'
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        obj.select_set(False)
        # Retain scan UVs while trimming lower neck/shoulders at a real plane.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                              dist=1e-6, plane_co=(0, 0, -.065), plane_no=(0, 0, 1), clear_inner=True)
        for vertex in bm.verts:
            vertex.co.z -= .0375
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

    mat = bpy.data.materials.new('Scan skin - color and normal')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .52
    bsdf.inputs['Metallic'].default_value = 0
    for filename, space, socket in [('Map-COL.jpg', 'sRGB', 'Base Color'),
                                     ('Infinite-Level_02_Tangent_SmoothUV.jpg', 'Non-Color', 'Normal')]:
        texture = nodes.new('ShaderNodeTexImage')
        texture.image = bpy.data.images.load(str(source / filename))
        texture.image.colorspace_settings.name = space
        texture.image.pack()
        output = texture.outputs['Color']
        if socket == 'Normal':
            normal = nodes.new('ShaderNodeNormalMap')
            normal.inputs['Strength'].default_value = .8
            links.new(output, normal.inputs['Color'])
            output = normal.outputs['Normal']
        links.new(output, bsdf.inputs[socket])
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    for directory in ('model', 'renders', 'reports'):
        (out / directory).mkdir(parents=True, exist_ok=True)
    (out / 'LICENSE-head.txt').write_bytes(license_bytes)
    bpy.ops.export_scene.gltf(filepath=str(out / 'model/head.glb'), export_format='GLB',
                              use_selection=True, export_yup=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_extras=True,
                              export_normals=True, export_tangents=True, export_texcoords=True)

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples, scene.cycles.use_denoising = args.samples, True
    scene.render.resolution_x, scene.render.resolution_y = args.resolution, round(args.resolution * 9 / 8)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format, scene.render.film_transparent = 'PNG', True
    scene.world = bpy.data.worlds.new('Studio ambient')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes['Background']
    background.inputs[0].default_value, background.inputs[1].default_value = (.12, .16, .22, 1), .25
    scene.view_settings.view_transform = 'AgX'

    def light(name, position, energy, color, size):
        data = bpy.data.lights.new(name, 'AREA')
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        data.energy, data.color, data.shape, data.size = energy, color, 'DISK', size
        obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()

    light('Large soft key', (-.40, -.50, .45), 8, (1, .86, .76), .45)
    light('Cool fill', (.40, -.25, .10), 3, (.66, .82, 1), .35)
    light('Rim', (.15, .25, .38), 12, (.66, .90, 1), .30)
    data = bpy.data.cameras.new('Review camera')
    camera = bpy.data.objects.new('Review camera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type, data.ortho_scale, data.lens = 'ORTHO', .255, 65
    views = {'front': (0, -.8, .025), 'threequarter': (.48, -.69, .025),
             'left_profile': (.8, 0, .025), 'right_profile': (-.8, 0, .025), 'under_nose': (.25, -.7, -.19)}
    renders = []
    if not args.skip_renders:
        clay = bpy.data.materials.new('Clay anatomy review')
        clay.use_nodes = True
        clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.38, .43, .48, 1)
        clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .72
        for prefix, material, selected in [('clay', clay, views), ('skin', mat, {k: views[k] for k in ('front', 'threequarter')})]:
            for obj in meshes:
                obj.data.materials[0] = material
            for name, position in selected.items():
                camera.location = position
                camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
                relative = f'renders/{prefix}_{name}.png'
                scene.render.filepath = str(out / relative)
                bpy.ops.render.render(write_still=True)
                renders.append(relative)
    for obj in meshes:
        obj.data.materials[0] = mat
    heights = [vertex.co.z for obj in meshes for vertex in obj.data.vertices]
    report = {
        'sourceAsset': 'Infinite, 3D Head Scan by Lee Perry-Smith (CC BY 3.0)',
        'modelRoute': 'EXISTING_MODEL_REVIEW_AND_WEB_EXPORT', 'blenderVersion': bpy.app.version_string,
        'meshCount': len(meshes), 'vertices': sum(len(obj.data.vertices) for obj in meshes),
        'triangles': sum(len(p.vertices) - 2 for obj in meshes for p in obj.data.polygons),
        'heightMeters': max(heights) - min(heights), 'renders': renders,
        'uvLayers': [layer.name for obj in meshes for layer in obj.data.uv_layers],
        'materials': 'Scan color and tangent normal; constant 0.52 roughness, metallic 0.',
        'gates': {'G0': 'SOURCE_ATTRIBUTION_COPIED_NOT_INDEPENDENTLY_VERIFIED',
                  'G1': 'REVIEW_RENDERED_CLAY' if renders else 'NOT_RUN',
                  'G2': 'REVIEW_RENDERED_FEATURES' if renders else 'NOT_RUN',
                  'G3': 'REVIEW_REQUIRED_NO_INDEPENDENT_LANDMARKS',
                  'G4': 'REUSED_SCAN_UV_AND_TEXTURES_NOT_NEW_SCULPT_OR_BAKE', 'G5': 'PENDING_BROWSER'},
        'releaseStatus': 'DEMONSTRATION_NOT_FINAL_RELEASE',
        'limitations': ['No independent measured landmarks or subject-specific photo-fit.',
                       'Normalized scan, open neck; not measured subject dimensions or watertight print mesh.',
                       'Closed eyes; no separate eyeballs, teeth, rig or hair.',
                       'Visual acceptance is subjective; no anatomical or identity certification.'],
    }
    (out / 'reports/build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'head-example.blend'), check_existing=False)
    print('BUILD_DONE', json.dumps(report), flush=True)


def main():
    parser, args, source, out, license_bytes = parse_args()
    try:
        import bpy
    except ImportError:
        parser.error('Use Blender --background --python-exit-code 1 --python SCRIPT -- [arguments]')
    if not bpy.app.background or bpy.app.version < (4, 2, 0):
        parser.error('Use isolated background Blender >=4.2')
    build(args, source, out, license_bytes)


if __name__ == '__main__':
    main()
