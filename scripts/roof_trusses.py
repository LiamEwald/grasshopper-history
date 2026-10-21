# category: roof trusses
# level: structure
# material: steel
# inside-view: hide
# gh-input: env_a float 130 100 150
# gh-input: env_b float 115 90 140
# gh-input: env_p float 2.4 2 4
# gh-input: env_h float 40 30 50
# gh-input: bulge float 0.03 0 0.08
# gh-input: cant float 50 30 60
# gh-input: roof_rise float 3 0 8
# gh-input: roof_drop float 4 0 10
# gh-input: trusses float 96 24 120
# gh-input: truss_d float 8 4 12
# gh-input: tip_d float 1.5 0.8 4
# gh-input: panels int 10 4 16
# gh-input: purlins int 11 0 24
# gh-input: support_every int 2 1 4
# Steel roof: `trusses` radial trusses cantilevering `cant` inwards from the envelope rim at
# env_h, depth truss_d at the rim tapering to tip_d, with panels diagonals; purlin rings tie them
# along the roof (RP-03); every support_every-th truss sits on a steel column (SC-012) from
# ground to the rim. The roof surface: plan a superellipse (env_a, env_b, exponent env_p),
# rising roof_rise and falling roof_drop towards the inner edge. Each truss is one element
# (RT-012, chords and diagonals together).
import math
import Rhino.Geometry as rg

n_t = int(trusses)


def rim(th):
    c, s = math.cos(th), math.sin(th)
    return rg.Point3d(env_a * math.copysign(abs(c) ** (2 / env_p), c), env_b * math.copysign(abs(s) ** (2 / env_p), s), 0)


def roof_pt(th, w):
    """Point on the roof surface at angle th, w from 0 (rim) to 1 (inner edge)."""
    p = rim(th)
    r = math.hypot(p.X, p.Y)
    k = 1 - w * cant / r
    return rg.Point3d(p.X * k, p.Y * k, env_h + roof_rise * 4 * w * (1 - w) - roof_drop * w)


def bar(mesh, p0, p1, b):
    d = p1 - p0
    if d.Length < 1e-6:
        return
    side = rg.Vector3d.CrossProduct(d, rg.Vector3d.ZAxis)
    if side.Length < 1e-6:
        side = rg.Vector3d.XAxis
    side.Unitize()
    box = rg.Box(rg.Plane(p0, d, side), rg.Interval(0, d.Length), rg.Interval(-b / 2, b / 2), rg.Interval(-b / 2, b / 2))
    mesh.Append(rg.Mesh.CreateFromBox(box, 1, 1, 1))


a, names, floors = [], [], []
n_p = int(panels)
for i in range(n_t):
    th = 2 * math.pi * i / n_t
    top = [roof_pt(th, j / float(n_p)) for j in range(n_p + 1)]
    bot = [rg.Point3d(p.X, p.Y, p.Z - (truss_d * (1 - j / float(n_p)) + tip_d * j / float(n_p))) for j, p in enumerate(top)]
    m = rg.Mesh()
    for j in range(n_p):
        bar(m, top[j], top[j + 1], 0.5)
        bar(m, bot[j], bot[j + 1], 0.5)
        bar(m, top[j], bot[j], 0.3)
        bar(m, bot[j], top[j + 1], 0.3)
    bar(m, top[-1], bot[-1], 0.3)
    m.Normals.ComputeNormals()
    a.append(m)
    names.append("RT-%03d" % (i + 1))
    if i % int(support_every) == 0:
        p = bot[0]
        a.append(rg.Box(rg.Plane.WorldXY, rg.Interval(p.X - 0.6, p.X + 0.6), rg.Interval(p.Y - 0.6, p.Y + 0.6),
                        rg.Interval(0.0, p.Z)).ToBrep())
        names.append("SC-%03d" % (i + 1))
for j in range(1, int(purlins) + 1):
    w = j / float(int(purlins) + 1)
    m = rg.Mesh()
    pts = [roof_pt(2 * math.pi * i / n_t, w) for i in range(n_t)]
    for i in range(n_t):
        p0, p1 = pts[i], pts[(i + 1) % n_t]
        bar(m, rg.Point3d(p0.X, p0.Y, p0.Z - 0.4), rg.Point3d(p1.X, p1.Y, p1.Z - 0.4), 0.3)
    m.Normals.ComputeNormals()
    a.append(m)
    names.append("RP-%02d" % j)
