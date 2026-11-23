"""Run with blender -b --factory-startup --python-exit-code 1 --python THIS_FILE."""
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import bpy
from mesh_uv_qa import inspect_object, intersection_area


class MeshUVTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def quad(self):
        mesh = bpy.data.meshes.new("quad")
        mesh.from_pydata([(0,0,0), (1,0,0), (1,1,0), (0,1,0)], [], [(0,1,2,3)])
        obj = bpy.data.objects.new("test", mesh)
        bpy.context.collection.objects.link(obj)
        layer = mesh.uv_layers.new(name="BakeUV")
        for loop in mesh.loops:
            layer.data[loop.index].uv = mesh.vertices[loop.vertex_index].co.xy
        return obj

    def qa(self, obj):
        return inspect_object(obj, bake=True)

    def test_valid_open_surface(self):
        r = self.qa(self.quad())
        self.assertTrue(r["passed"], r)
        self.assertAlmostEqual(r["uv"]["stretch_max"], 1)

    def test_closed_policy(self):
        self.assertFalse(inspect_object(self.quad(), require_closed=True)["passed"])

    def test_missing_uv(self):
        o = self.quad(); o.data.uv_layers.remove(o.data.uv_layers.active)
        self.assertIn("missing_uv", self.qa(o)["errors"])

    def test_collapsed_uv(self):
        o = self.quad()
        for l in o.data.uv_layers.active.data: l.uv = (0,0)
        self.assertIn("uv_degenerate_triangles", self.qa(o)["errors"])

    def test_out_of_tile(self):
        o = self.quad(); o.data.uv_layers.active.data[0].uv = (2,2)
        self.assertIn("uv_outside_0_1", self.qa(o)["errors"])

    def test_stretch(self):
        o = self.quad()
        for l in o.data.uv_layers.active.data: l.uv.x *= .001
        self.assertIn("uv_stretch_limit", self.qa(o)["errors"])

    def test_absolute_density_rejects_under_resolved_atlas(self):
        o=self.quad()
        r=inspect_object(o,bake=True,resolution=128,min_texels_per_cm=2)
        self.assertIn('uv_absolute_texel_density_limit',r['errors'])

    def test_overlap_on_separate_islands(self):
        o = self.quad(); m = o.data
        m.clear_geometry()
        m.from_pydata([(0,0,0),(1,0,0),(0,1,0),(2,0,0),(3,0,0),(2,1,0)], [], [(0,1,2),(3,4,5)])
        uv = m.uv_layers.active or m.uv_layers.new(name="BakeUV")
        for i,l in enumerate(uv.data): l.uv = [(0,0),(1,0),(0,1)][i%3]
        self.assertIn("uv_overlap", self.qa(o)["errors"])

    def test_degenerate_mesh(self):
        o = self.quad(); o.data.vertices[1].co = o.data.vertices[0].co
        self.assertIn("degenerate_mesh_triangles", self.qa(o)["errors"])

    def test_negative_scale(self):
        o = self.quad(); o.scale.x=-1; bpy.context.view_layer.update()
        self.assertIn("negative_or_singular_transform: apply and verify normals on a working copy", self.qa(o)["errors"])

    def test_loose_vertex_and_duplicate_face(self):
        o=self.quad();o.data.clear_geometry()
        o.data.from_pydata([(0,0,0),(1,0,0),(0,1,0),(8,8,8)], [], [(0,1,2),(0,1,2)])
        r=self.qa(o)
        self.assertIn("loose_vertices",r["errors"])
        self.assertIn("duplicate_faces",r["errors"])

    def test_nonmanifold_edge(self):
        o=self.quad();o.data.clear_geometry()
        o.data.from_pydata([(0,0,0),(1,0,0),(0,1,0),(0,-1,0),(0,0,1)], [], [(0,1,2),(1,0,3),(0,1,4)])
        self.assertIn("nonmanifold_edges",self.qa(o)["errors"])

    def test_shared_edge_not_overlap(self):
        self.assertEqual(intersection_area([(0,0),(1,0),(0,1)],[(1,0),(1,1),(0,1)]),0)

    def test_inward_closed_mesh(self):
        import bmesh
        bpy.ops.mesh.primitive_cube_add()
        obj=bpy.context.object
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free()
        self.assertIn("inward_closed_components", self.qa(obj)["errors"])

    def test_island_padding(self):
        o=self.quad();m=o.data;m.clear_geometry()
        m.from_pydata([(0,0,0),(1,0,0),(0,1,0),(2,0,0),(3,0,0),(2,1,0)],[],[(0,1,2),(3,4,5)])
        uv=m.uv_layers.active or m.uv_layers.new(name="BakeUV")
        for i,l in enumerate(uv.data):
            l.uv=[(.1,.1),(.4,.1),(.1,.4),(.401,.1),(.7,.1),(.401,.4)][i]
        self.assertIn("uv_island_padding",inspect_object(o,bake=True,resolution=1024,min_gap_px=8)["errors"])

    def test_all_reference_presets(self):
        import json
        from build_reference import Builder
        from mesh_uv_qa import inspect
        for path in sorted((Path(__file__).resolve().parents[1]/"assets").glob("ref-*.json")):
            with self.subTest(preset=path.name):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                col=Builder(json.loads(path.read_text(encoding="utf-8"))).build()
                r=inspect(col.all_objects)
                self.assertTrue(r["passed"],[(o['object'],o['errors']) for o in r['objects'] if not o['passed']])

    def test_bake_atlas_repairs_only_overlapping_uv(self):
        from bake_web_pbr import finish_atlas
        o=self.quad();m=o.data;m.clear_geometry()
        m.from_pydata([(0,0,0),(1,0,0),(0,1,0),(2,0,0),(3,0,0),(2,1,0)],[],[(0,1,2),(3,4,5)])
        uv=m.uv_layers.active or m.uv_layers.new(name="BakeUV")
        for i,l in enumerate(uv.data):l.uv=[(0,0),(1,0),(0,1)][i%3]
        source=m.uv_layers.new(name="SourceUV")
        for i,l in enumerate(source.data):l.uv=(i/10,.7)
        before=[tuple(l.uv) for l in source.data]
        geometry=[tuple(v.co) for v in m.vertices]
        m.uv_layers.active=uv
        o.select_set(True);bpy.context.view_layer.objects.active=o
        repair=finish_atlas(o,256,2)
        self.assertEqual(repair['split_triangles'],2)
        self.assertEqual(before,[tuple(l.uv) for l in m.uv_layers['SourceUV'].data])
        self.assertEqual(geometry,[tuple(v.co) for v in m.vertices])
        self.assertTrue(inspect_object(o,uv_name='BakeUV',bake=True,resolution=256,min_gap_px=4)['passed'])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MeshUVTests))
    if not result.wasSuccessful(): raise SystemExit(1)
