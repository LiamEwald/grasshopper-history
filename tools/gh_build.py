"""Rebuild model.gh from scripts/*.py and show the result in Rhino. Runs inside Rhino.

One labelled Python 3 component per script, outputs a / names / floors / stats.
Inputs with the same name share one slider. The canvas stays hidden; Rhino shows the
model in plain grey on the layer "Model". Always writes .history/tmp/build.json
(rhinocode returns early and swallows exceptions).
"""
import glob
import json
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT = os.path.join(ROOT, ".history", "tmp", "build.json")
GH_PATH = os.path.join(ROOT, "model.gh")
OUTPUTS = ["a", "names", "floors", "stats"]
LIVE = "Model"


def write_result(data):
    os.makedirs(os.path.dirname(RESULT), exist_ok=True)
    with open(RESULT + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(RESULT + ".tmp", RESULT)


def parse_inputs(source):
    inputs = []
    for line in source.splitlines():
        if line.startswith("# gh-input:"):
            name, kind, default, lo, hi = line.split(":", 1)[1].split()[:5]
            inputs.append({"name": name, "kind": kind, "default": float(default),
                           "min": float(lo), "max": float(hi)})
    return inputs


try:
    import System
    import Rhino
    Rhino.RhinoApp.GetPlugInObject("Grasshopper").LoadEditor()  # a fresh Rhino has Grasshopper (and its Python components) unloaded
    import Grasshopper as gh
    from Grasshopper.Kernel.Special import GH_NumberSlider
    from Grasshopper.GUI.Base import GH_SliderAccuracy
    from RhinoCodePluginGH.Components import Python3Component
    from RhinoCodePluginGH.Parameters import ScriptVariableParam

    def make_slider(spec, x, y):
        s = GH_NumberSlider()
        s.CreateAttributes()
        s.NickName = spec["name"]
        is_int = spec["kind"] == "int"
        s.Slider.Type = GH_SliderAccuracy.Integer if is_int else GH_SliderAccuracy.Float
        s.Slider.DecimalPlaces = 0 if is_int else 2
        s.Slider.Minimum = System.Decimal(spec["min"])
        s.Slider.Maximum = System.Decimal(spec["max"])
        s.Slider.Value = System.Decimal(spec["default"])
        s.Attributes.Pivot = System.Drawing.PointF(x, y)
        return s

    def make_component(name, source, inputs, x, y):
        comp = Python3Component.Create(name, source, None, True)
        comp.NickName = name
        comp.MarshInputs = True
        comp.MarshOutputs = True
        for spec in inputs:
            p = ScriptVariableParam(spec["name"])
            p.Name = p.NickName = spec["name"]
            comp.Params.RegisterInputParam(p)
        for out in OUTPUTS:
            p = ScriptVariableParam(out)
            p.Name = p.NickName = out
            comp.Params.RegisterOutputParam(p)
        comp.Params.OnParametersChanged()
        comp.VariableParameterMaintenance()
        comp.CreateAttributes()
        comp.Attributes.Pivot = System.Drawing.PointF(x, y)
        return comp

    def show_live(comps):
        """The current model, in grey, on its own layer. Only a build (a new version or a restore) touches it."""
        rdoc = Rhino.RhinoDoc.ActiveDoc
        idx = rdoc.Layers.FindByFullPath(LIVE, -1)
        if idx < 0:
            idx = rdoc.Layers.Add(LIVE, System.Drawing.Color.FromArgb(190, 190, 190))
        for obj in list(rdoc.Objects.FindByLayer(rdoc.Layers[idx]) or []):
            rdoc.Objects.Delete(obj, True)
        attr = Rhino.DocObjects.ObjectAttributes()
        attr.LayerIndex = idx
        for comp in comps.values():
            comp.Hidden = True
            for p in comp.Params.Output:
                if p.NickName == "a":
                    for goo in p.VolatileData.AllData(True):
                        geo = goo.ScriptVariable() if hasattr(goo, "ScriptVariable") else None
                        if isinstance(geo, Rhino.Geometry.GeometryBase):
                            rdoc.Objects.Add(geo, attr)
        rdoc.Views.Redraw()

    def main():
        plugin = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        plugin.LoadEditor()
        server = gh.Instances.DocumentServer
        for old in list(server):
            if old.FilePath and os.path.normcase(old.FilePath) == os.path.normcase(GH_PATH):
                server.RemoveDocument(old)
                old.Dispose()  # free the previous solution; a long session otherwise runs out of memory

        doc = gh.Kernel.GH_Document()
        sliders, values, comps = {}, {}, {}
        for i, path in enumerate(sorted(glob.glob(os.path.join(ROOT, "scripts", "*.py")))):
            name = os.path.splitext(os.path.basename(path))[0]
            source = open(path, encoding="utf-8").read()
            inputs = parse_inputs(source)
            comp = make_component(name, source, inputs, 420, 60 + i * 200)
            doc.AddObject(comp, False)
            for j, spec in enumerate(inputs):
                if spec["name"] not in sliders:
                    s = make_slider(spec, 60, 30 + len(sliders) * 26)
                    doc.AddObject(s, False)
                    sliders[spec["name"]] = s
                    values[spec["name"]] = spec["default"]
                comp.Params.Input[j].AddSource(sliders[spec["name"]])
            comps[name] = comp

        server.AddDocument(doc)
        gh.Instances.ActiveCanvas.Document = doc
        doc.FilePath = GH_PATH
        doc.NewSolution(True)
        gh.Kernel.GH_DocumentIO(doc).SaveQuiet(GH_PATH)

        errors = {}
        for name, comp in comps.items():
            msgs = []
            for level, tag in ((gh.Kernel.GH_RuntimeMessageLevel.Error, "error"),
                               (gh.Kernel.GH_RuntimeMessageLevel.Warning, "warning")):
                msgs += [{"level": tag, "text": str(m)} for m in comp.RuntimeMessages(level)]
            if msgs:
                errors[name] = msgs
        show_live(comps)
        plugin.HideEditor()
        write_result({"ok": True, "scripts": list(comps), "values": values, "errors": errors})

    main()
except Exception:
    write_result({"ok": False, "error": traceback.format_exc()})
