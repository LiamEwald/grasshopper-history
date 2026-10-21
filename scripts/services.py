# category: ventilation and drainage
# level: mep
# material: steel
# gh-input: pitch_l float 105 90 120
# gh-input: pitch_w float 68 60 90
# gh-input: runoff float 7.5 3 15
# gh-input: corner_r float 20 0 60
# gh-input: env_a float 130 100 150
# gh-input: env_b float 115 90 140
# gh-input: env_p float 2.4 2 4
# gh-input: env_z0 float 12 0 20
# gh-input: env_h float 40 30 50
# gh-input: ahu_n int 20 0 30
# gh-input: duct_d float 1.0 0.4 1.6
# gh-input: duct_ring float 30 10 60
# gh-input: down_n int 24 0 48
# Ventilation: ahu_n air-handling units (6 x 3 x 3 m) on a ring duct_ring behind the first row
# (AHU-07), joined by a supply ring duct of diameter duct_d under the tier 1 concourse (SD-1).
# Drainage: a roof gutter on the envelope rim (GU-1) and down_n downpipes (DP-07, 200 mm) from
# the rim to the plinth top.
import math
import Rhino.Geometry as rg


def rim(th):
    c, s = math.cos(th), math.sin(th)
    return rg.Point3d(env_a * math.copysign(abs(c) ** (2 / env_p), c), env_b * math.copysign(abs(s) ** (2 / env_p), s), 0)


def ring_pt(t, d):
    hx, hy = pitch_l / 2 + d, pitch_w / 2 + d
    c, s = math.cos(t), math.sin(t)
    return rg.Point3d(hx * math.copysign(abs(c) ** 0.4, c), hy * math.copysign(abs(s) ** 0.4, s), 0)


def bar(mesh, p0, p1, b):
    d = p1 - p0
    side = rg.Vector3d.CrossProduct(d, rg.Vector3d.ZAxis)
    if side.Length < 1e-6:
        side = rg.Vector3d.XAxis
    side.Unitize()
    box = rg.Box(rg.Plane(p0, d, side), rg.Interval(0, d.Length), rg.Interval(-b / 2, b / 2), rg.Interval(-b / 2, b / 2))
    mesh.Append(rg.Mesh.CreateFromBox(box, 1, 1, 1))


a, names, floors = [], [], []
n = int(ahu_n)
z_duct = 4.5
if n:
    for i in range(n):
        p = ring_pt(2 * math.pi * i / n, duct_ring)
        a.append(rg.Box(rg.Plane(rg.Point3d(p.X, p.Y, 1.5), rg.Vector3d(-p.Y, p.X, 0), rg.Vector3d(p.X, p.Y, 0)),
                        rg.Interval(-3, 3), rg.Interval(-1.5, 1.5), rg.Interval(-1.5, 1.5)).ToBrep())
        names.append("AHU-%02d" % (i + 1))
    m = rg.Mesh()
    seg = 64
    for i in range(seg):
        p0, p1 = ring_pt(2 * math.pi * i / seg, duct_ring), ring_pt(2 * math.pi * (i + 1) / seg, duct_ring)
        bar(m, rg.Point3d(p0.X, p0.Y, z_duct), rg.Point3d(p1.X, p1.Y, z_duct), duct_d)
    a.append(m)
    names.append("SD-1")
k = int(down_n)
if k:
    m = rg.Mesh()
    seg = 96
    for i in range(seg):
        p0, p1 = rim(2 * math.pi * i / seg), rim(2 * math.pi * (i + 1) / seg)
        bar(m, rg.Point3d(p0.X, p0.Y, env_h + 0.2), rg.Point3d(p1.X, p1.Y, env_h + 0.2), 0.4)
    a.append(m)
    names.append("GU-1")
    for i in range(k):
        p = rim(2 * math.pi * (i + 0.5) / k)
        a.append(rg.Brep.CreatePipe(rg.LineCurve(rg.Point3d(p.X * 0.995, p.Y * 0.995, env_z0),
                                                 rg.Point3d(p.X * 0.995, p.Y * 0.995, env_h)),
                                    0.1, False, rg.PipeCapMode.Flat, True, 0.001, 0.01)[0])
        names.append("DP-%02d" % (i + 1))
