# category: lighting
# level: mep
# material: steel
# gh-input: env_a float 130 100 150
# gh-input: env_b float 115 90 140
# gh-input: env_p float 2.4 2 4
# gh-input: env_z0 float 12 0 20
# gh-input: env_h float 40 30 50
# gh-input: bulge float 0.03 0 0.08
# gh-input: cant float 50 30 60
# gh-input: roof_rise float 3 0 8
# gh-input: roof_drop float 4 0 10
# gh-input: truss_d float 9 4 12
# gh-input: tip_d float 1.5 0.8 4
# gh-input: rings_f int 10 4 16
# gh-input: flood_n int 160 0 400
# gh-input: facade_rings int 12 0 16
# gh-input: led int 0 0 1
# Floodlights: flood_n fittings (1.2 x 0.6 x 0.6 m) along the bottom chord at the roof's inner
# edge (FL-012). Facade lighting: luminaire strips along facade_rings facade rings behind the
# cushions (LF-03): 300 x 200 mm housings, or 80 x 60 mm LED strips with led = 1.
import math
import Rhino.Geometry as rg


def rim(th):
    c, s = math.cos(th), math.sin(th)
    return rg.Point3d(env_a * math.copysign(abs(c) ** (2 / env_p), c), env_b * math.copysign(abs(s) ** (2 / env_p), s), 0)


def bar(mesh, p0, p1, b, h):
    d = p1 - p0
    side = rg.Vector3d.CrossProduct(d, rg.Vector3d.ZAxis)
    side.Unitize()
    box = rg.Box(rg.Plane(p0, d, side), rg.Interval(0, d.Length), rg.Interval(-b / 2, b / 2), rg.Interval(-h / 2, h / 2))
    mesh.Append(rg.Mesh.CreateFromBox(box, 1, 1, 1))


a, names, floors = [], [], []
n = int(flood_n)
for i in range(n):
    th = 2 * math.pi * i / n
    p = rim(th)
    r = math.hypot(p.X, p.Y)
    k = 1 - cant / r
    z = env_h - roof_drop - tip_d - 0.6
    c = rg.Point3d(p.X * k, p.Y * k, z)
    a.append(rg.Box(rg.Plane(c, rg.Vector3d(p.X, p.Y, 0), rg.Vector3d(-p.Y, p.X, 0)),
                    rg.Interval(-0.6, 0.6), rg.Interval(-0.3, 0.3), rg.Interval(-0.3, 0.3)).ToBrep())
    names.append("FL-%03d" % (i + 1))
nf = int(rings_f)
for j in range(int(facade_rings)):
    t = (j + 0.5) / max(int(facade_rings), 1)
    z = env_z0 + (env_h - env_z0) * t
    kk = (1 + bulge * math.sin(math.pi * t)) - 0.6 / env_a
    m = rg.Mesh()
    seg = 96
    pts = [rim(2 * math.pi * i / seg) for i in range(seg)]
    for i in range(seg):
        p0, p1 = pts[i], pts[(i + 1) % seg]
        bar(m, rg.Point3d(p0.X * kk, p0.Y * kk, z), rg.Point3d(p1.X * kk, p1.Y * kk, z),
            0.08 if int(led) else 0.3, 0.06 if int(led) else 0.2)
    a.append(m)
    names.append("LF-%02d" % (j + 1))
