# category: massing studies
# level: massing
# material: massing
# gh-input: m_type int 0 0 3
# gh-input: m_a float 130 80 160
# gh-input: m_b float 115 80 160
# gh-input: m_p float 2 2 6
# gh-input: m_h float 50 20 60
# gh-input: m_flare float 0 -0.15 0.25
# gh-input: m_open float 0.62 0.4 0.8
# Rough volumes before any detail, one closed solid per mass.
#   m_type 0: one ring, plan a superellipse with half-axes m_a, m_b and exponent m_p
#            (2 = ellipse, higher = squarer), m_h high, the top flaring outwards by m_flare
#            (negative: leaning in). The open centre is m_open of the plan at the top,
#            narrowing to 80 % of that at the bottom, like a raked bowl.
#   m_type 1: four separate stands around the pitch, each m_h high (M-N, M-S, M-E, M-W).
#   m_type 2: the ring as a circle of radius (m_a + m_b) / 2.
#   m_type 3: a ring on a rectangle with chamfered corners (m_a by m_b).
# Names M-RING or M-N/S/E/W. Their volume shows as the massing volume.
import math
import Rhino.Geometry as rg


def outline(a, b, p, z, kind):
    pts = []
    n = 96
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        if kind == 2:
            r = (a + b) / 2
            pts.append(rg.Point3d(r * c, r * s, z))
        elif kind == 3:
            m = max(abs(c) / a, abs(s) / b, (abs(c) + abs(s)) / (0.85 * (a + b)))  # chamfered rectangle
            pts.append(rg.Point3d(c / m, s / m, z))
        else:
            pts.append(rg.Point3d(a * math.copysign(abs(c) ** (2 / p), c), b * math.copysign(abs(s) ** (2 / p), s), z))
    return rg.Polyline(pts).ToNurbsCurve()


def ring(kind):
    """Closed ring: outer wall, inner (bowl) wall, top and bottom annuli, joined."""
    k, o = 1 + m_flare, m_open
    ob, ot = outline(m_a, m_b, m_p, 0, kind), outline(m_a * k, m_b * k, m_p, m_h, kind)
    ib, it = outline(m_a * o * 0.8, m_b * o * 0.8, m_p, 0, kind), outline(m_a * o * k, m_b * o * k, m_p, m_h, kind)
    loft = lambda c0, c1: rg.Brep.CreateFromLoft([c0, c1], rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Straight, False)[0]
    parts = [loft(ob, ot), loft(ib, it)] + list(rg.Brep.CreatePlanarBreps([ot, it], 0.01)) + list(rg.Brep.CreatePlanarBreps([ob, ib], 0.01))
    joined = rg.Brep.JoinBreps(parts, 0.01)
    return joined[0] if joined else parts[0]


a, names, floors, stats = [], [], [], []
kind = int(m_type)
if kind == 1:
    pl, pw = 52.5 + 8, 34 + 8
    d = (m_b - pw) * 0.75
    e = (m_a - pl) * 0.75
    for tag, x0, x1, y0, y1 in (("M-S", -pl, pl, -pw - d, -pw), ("M-N", -pl, pl, pw, pw + d),
                                ("M-W", -pl - e, -pl, -pw, pw), ("M-E", pl, pl + e, -pw, pw)):
        a.append(rg.Box(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(0, m_h)).ToBrep())
        names.append(tag)
else:
    a.append(ring(kind))
    names.append("M-RING")
