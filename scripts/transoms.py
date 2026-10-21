# category: envelope transoms
# level: structure
# material: steel
# inside-view: hide
# gh-input: env_a float 130 100 150
# gh-input: env_b float 115 90 140
# gh-input: env_p float 2.4 2 4
# gh-input: env_z0 float 12 0 20
# gh-input: env_h float 40 30 50
# gh-input: bulge float 0.03 0 0.08
# gh-input: cant float 50 30 60
# gh-input: roof_rise float 3 0 8
# gh-input: roof_drop float 4 0 10
# gh-input: env_div int 192 48 240
# gh-input: rings_f int 10 4 16
# gh-input: rings_r int 21 0 30
# gh-input: env_on int 3 0 3
# Steel substructure the cushions are clamped to: a ring transom on every envelope ring
# (TR-04) and the two families of diagonal lines that form the rhomboids (DA-012, DB-012),
# 200 mm members, over the parts of the envelope that have cushions (env_on as in envelope.py).
import math
import Rhino.Geometry as rg


def rim(th):
    c, s = math.cos(th), math.sin(th)
    return rg.Point3d(env_a * math.copysign(abs(c) ** (2 / env_p), c), env_b * math.copysign(abs(s) ** (2 / env_p), s), 0)


def point(i, j):
    th = 2 * math.pi * i / env_div
    p = rim(th)
    nf, nr = int(rings_f), int(rings_r)
    if j <= nf:
        t = j / float(nf)
        k = 1 + bulge * math.sin(math.pi * t)
        return rg.Point3d(p.X * k, p.Y * k, env_z0 + (env_h - env_z0) * t)
    w = (j - nf) / float(nr)
    r = math.hypot(p.X, p.Y)
    k = 1 - w * cant / r
    return rg.Point3d(p.X * k, p.Y * k, env_h + roof_rise * 4 * w * (1 - w) - roof_drop * w + 0.15)


def bar(mesh, p0, p1, b=0.2):
    d = p1 - p0
    side = rg.Vector3d.CrossProduct(d, rg.Vector3d.ZAxis)
    if side.Length < 1e-6:
        side = rg.Vector3d.XAxis
    side.Unitize()
    box = rg.Box(rg.Plane(p0, d, side), rg.Interval(0, d.Length), rg.Interval(-b / 2, b / 2), rg.Interval(-b / 2, b / 2))
    mesh.Append(rg.Mesh.CreateFromBox(box, 1, 1, 1))


n = int(env_div)
nf, nr = int(rings_f), int(rings_r)
on = int(env_on)
j0 = 0 if on in (1, 3) else nf
j1 = nf + nr if on in (2, 3) else nf
a, names, floors = [], [], []
if on:
    for j in range(j0, j1 + 1):
        if j % 2:
            continue  # ring transoms on the rings through the cushion corners
        m = rg.Mesh()
        for i in range(n):
            bar(m, point(i, j), point(i + 1, j))
        a.append(m)
        names.append("TR-%02d" % j)
    for fam, step in (("DA", 1), ("DB", -1)):
        for i in range(0, n, 2):
            m = rg.Mesh()
            for j in range(j0, j1):
                bar(m, point(i + step * (j - j0), j), point(i + step * (j - j0 + 1), j + 1))
            a.append(m)
            names.append("%s-%03d" % (fam, i // 2 + 1))
