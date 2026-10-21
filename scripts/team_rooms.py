# category: team rooms
# level: interior
# material: timber
# gh-input: pitch_l float 105 90 120
# gh-input: pitch_w float 68 60 90
# gh-input: runoff float 7.5 3 15
# gh-input: rooms_n int 8 0 8
# gh-input: room_w float 9 6 14
# gh-input: room_d float 12 8 18
# gh-input: tunnel_w float 5 3 8
# Team rooms at pitch level under the west stand, behind the first columns: a players' tunnel
# tunnel_w wide on the halfway line, and rooms_n rooms (changing rooms, referees, medical) room_w
# by room_d split either side of it, as 200 mm walls 3.2 m high. Names TM-TW (tunnel walls), TM-W2 (room walls), TM-WB (back walls).
import Rhino.Geometry as rg

a, names, floors = [], [], []
y0 = -(pitch_w / 2 + runoff + 6)  # behind the first raker columns on the south (main) side
y1 = y0 - room_d


def wall(x0, x1, ya, yb, name):
    a.append(rg.Box(rg.Plane.WorldXY, rg.Interval(min(x0, x1), max(x0, x1)), rg.Interval(min(ya, yb), max(ya, yb)),
                    rg.Interval(0.0, 3.2)).ToBrep())
    names.append(name)


n = int(rooms_n)
if n:
    for s, x in (("W", -tunnel_w / 2), ("E", tunnel_w / 2)):
        wall(x - 0.1, x + 0.1, y0, y1 - 4, "TM-T" + s)
    left = n // 2
    right = n - left
    for side, count, sx in (("W", left, -1), ("E", right, 1)):
        for k in range(count + 1):
            x = sx * (tunnel_w / 2 + k * room_w)
            wall(x - 0.1, x + 0.1, y0, y1, "TM-%s%d" % (side, k + 1))
        if count:
            x_end = sx * (tunnel_w / 2 + count * room_w)
            wall(sx * tunnel_w / 2, x_end, y1 - 0.1, y1 + 0.1, "TM-%sB" % side)
