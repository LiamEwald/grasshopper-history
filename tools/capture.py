"""Pictures of the model Grasshopper just solved, with what changed in red. Runs inside Rhino.

Reads .history/tmp/capture.json:
  changed: element names to draw red (new or changed against the parent version)
  removed: boxes [x0,y0,z0,x1,y1,z1] of elements that are gone, drawn as red outlines
  inside:  also take the inside view: envelope, upper slabs and scripts marked
           "# inside-view: hide" (a roof structure, say) are hidden
Writes .history/tmp/cap-<side>.png from each corner (ne, nw, se, sw) on a transparent
background, plus cap-inside-<side>.png; autosave keeps the corner that shows the most red.
Every other layer is hidden while capturing and the user's view is put back.
"""
import json
import math
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, ".history", "tmp")
RESULT = os.path.join(TMP, "capture-result.json")
GH_PATH = os.path.join(ROOT, "model.gh")
SIZE = (1600, 1200)
SIDES = {"se": (1, -1), "sw": (-1, -1), "ne": (1, 1), "nw": (-1, 1)}
GREY = (215, 215, 212)
RED = (214, 40, 40)


def write_result(data):
    with open(RESULT + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(RESULT + ".tmp", RESULT)


def header(name, key, default):
    try:
        for line in open(os.path.join(ROOT, "scripts", name + ".py"), encoding="utf-8"):
            if line.startswith("# %s:" % key):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return default


try:
    import System
    import Rhino
    import Rhino.Geometry as rg
    import Grasshopper as gh

    def find_doc():
        for d in gh.Instances.DocumentServer:
            if d.FilePath and os.path.normcase(d.FilePath) == os.path.normcase(GH_PATH):
                return d
        raise RuntimeError("model.gh is not open; run gh_build first")

    def output(comp, nick):
        for p in comp.Params.Output:
            if p.NickName == nick:
                return [goo.ScriptVariable() if hasattr(goo, "ScriptVariable") else goo
                        for goo in p.VolatileData.AllData(True)]
        return []

    def color(c):
        return System.Drawing.Color.FromArgb(*c)

    def add(rdoc, geo, layer, c):
        attr = Rhino.DocObjects.ObjectAttributes()
        attr.LayerIndex = layer
        attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        attr.ObjectColor = color(c)
        attr.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
        return rdoc.Objects.Add(geo, attr)

    def main():
        with open(os.path.join(TMP, "capture.json"), encoding="utf-8") as f:
            req = json.load(f)
        changed = set(req.get("changed", []))
        doc = find_doc()
        rdoc = Rhino.RhinoDoc.ActiveDoc

        layer = rdoc.Layers.FindByFullPath("_capture", -1)
        if layer < 0:
            layer = rdoc.Layers.Add("_capture", color(GREY))
        envelope, ids, box = [], [], rg.BoundingBox.Empty
        for comp in doc.Objects:
            if not hasattr(comp, "Params") or not any(p.NickName == "names" for p in comp.Params.Output):
                continue
            cat = header(comp.NickName, "category", "")
            outer = (header(comp.NickName, "level", "structure") == "envelope" or cat == "slabs"
                     or header(comp.NickName, "inside-view", "") == "hide")
            names = [str(n) for n in output(comp, "names")]
            for i, g in enumerate(output(comp, "a")):
                if isinstance(g, (rg.Extrusion, rg.Box)):
                    g = g.ToBrep()
                if not isinstance(g, rg.GeometryBase):
                    continue
                name = names[i] if i < len(names) else None
                oid = add(rdoc, g, layer, RED if name in changed else GREY)
                ids.append(oid)
                box.Union(g.GetBoundingBox(True))
                if outer and name != "S-0":  # the Inside view keeps the ground slab to stand on
                    envelope.append(oid)
        for b in req.get("removed", []):  # gone: a red outline where it was
            bb = rg.BoundingBox(rg.Point3d(*b[:3]), rg.Point3d(*b[3:]))
            for edge in rg.Box(bb).ToBrep().Edges:
                ids.append(add(rdoc, edge.DuplicateCurve(), layer, RED))
            box.Union(bb)

        view = rdoc.Views.Find("Perspective", False) or rdoc.Views.ActiveView
        vp = view.ActiveViewport
        saved = Rhino.DocObjects.ViewportInfo(vp)
        saved_mode = vp.DisplayMode
        shown = [l for l in rdoc.Layers if l.IsVisible and not l.IsDeleted and l.Index != layer]
        for l in shown:  # only the capture copy is in the picture
            l.IsVisible = False
        written = []
        try:
            mode = Rhino.Display.DisplayModeDescription.FindByName("Shaded")
            if mode:
                vp.DisplayMode = mode
            vp.ChangeToPerspectiveProjection(False, 50.0)
            target = box.Center
            radius = box.Diagonal.Length / 2.0

            def grab(path):
                vc = Rhino.Display.ViewCapture()
                vc.Width, vc.Height = SIZE
                vc.ScaleScreenItems = False
                vc.DrawAxes = vc.DrawGrid = vc.DrawGridAxes = False
                vc.TransparentBackground = True
                bmp = vc.CaptureToBitmap(view)
                bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png)
                bmp.Dispose()
                written.append(os.path.basename(path))

            for side, (sx, sy) in SIDES.items():
                d = rg.Vector3d(sx, sy, 0.8)
                d.Unitize()
                vp.SetCameraLocations(target, target + d * (radius / math.sin(math.radians(14))))
                vp.CameraUp = rg.Vector3d.ZAxis
                vp.ZoomBoundingBox(box)
                view.Redraw()
                grab(os.path.join(TMP, "cap-%s.png" % side))
                if req.get("inside") and envelope:  # nothing to hide: the inside view would repeat the outside
                    for i in envelope:
                        rdoc.Objects.Hide(i, True)
                    view.Redraw()
                    grab(os.path.join(TMP, "cap-inside-%s.png" % side))
                    for i in envelope:
                        rdoc.Objects.Show(i, True)
        finally:
            for i in ids:
                rdoc.Objects.Delete(i, True)
            for l in shown:
                l.IsVisible = True
            vp.SetViewProjection(saved, True)
            vp.DisplayMode = saved_mode
            view.Redraw()
        rdoc.ClearUndoRecords(True)  # the temporary capture objects would otherwise pile up in the undo stack
        System.GC.Collect()
        write_result({"ok": True, "files": written})

    main()
except Exception:
    write_result({"ok": False, "error": traceback.format_exc()})
