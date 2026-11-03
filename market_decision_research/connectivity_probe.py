"""Static counterexample probe, not a closed-loop driving or literature benchmark.

Checks whether collision-free stopped vehicle poses preserve one pedestrian OD
connection. Uses conservative cell clearance and a conservative envelope for
bounded vehicle pose errors. No human response, motion prediction, or MPC.
"""
from collections import deque
from pathlib import Path
import csv
import json
import math
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'probe'
OUT.mkdir(exist_ok=True)
CAR_LENGTH, CAR_WIDTH = 4.5, 1.8
EFFECTIVE_PED_RADIUS = 0.40  # Test assumption: body radius plus clearance.
POSITION_ERROR, YAW_ERROR = 0.15, math.radians(3)
CAR_RADIUS = math.hypot(CAR_LENGTH / 2, CAR_WIDTH / 2)
ENVELOPE_PAD = POSITION_ERROR + 2 * CAR_RADIUS * math.sin(YAW_ERROR / 2)

def rect_distance(xx, yy, cx, cy, length, width, yaw=0):
    dx, dy = xx - cx, yy - cy
    local_x = dx * math.cos(yaw) + dy * math.sin(yaw)
    local_y = -dx * math.sin(yaw) + dy * math.cos(yaw)
    return np.hypot(np.maximum(np.abs(local_x) - length / 2, 0),
                    np.maximum(np.abs(local_y) - width / 2, 0))

def grid(throat_width, resolution, pose=None, pad=0):
    nx, ny = round(24 / resolution), round(10 / resolution)
    x = (np.arange(nx) + .5) * resolution
    y = (np.arange(ny) + .5) * resolution
    xx, yy = np.meshgrid(x, y)
    margin = EFFECTIVE_PED_RADIUS + resolution / math.sqrt(2)
    free = (xx > margin) & (xx < 24 - margin) & (yy > margin) & (yy < 10 - margin)
    stall_height = (10 - throat_width) / 2
    for cy in (stall_height / 2, 10 - stall_height / 2):
        free &= rect_distance(xx, yy, 12.5, cy, 5, stall_height) > margin
    if pose is not None:
        free &= rect_distance(xx, yy, *pose[:2], CAR_LENGTH, CAR_WIDTH, pose[2]) > margin + pad
    return free, x, y

def path_between(free, x, y):
    # Ports are potential corridor entry/exit points, not simulated agents.
    start = (int(np.argmin(abs(y - 5))), int(np.argmin(abs(x - 1))))
    goal = (int(np.argmin(abs(y - 5))), int(np.argmin(abs(x - 23))))
    if not free[start] or not free[goal]:
        return None
    seen = np.zeros_like(free, dtype=bool)
    seen[start] = True
    parent = {}
    queue = deque([start])
    ny, nx = free.shape
    while queue:
        current = queue.popleft()
        if current == goal:
            nodes = [goal]
            while nodes[-1] != start:
                nodes.append(parent[nodes[-1]])
            return np.array([(x[c], y[r]) for r, c in reversed(nodes)])
        r, c = current
        for nr, nc in ((r+1,c), (r-1,c), (r,c+1), (r,c-1)):
            if 0 <= nr < ny and 0 <= nc < nx and free[nr,nc] and not seen[nr,nc]:
                seen[nr,nc] = True
                parent[(nr,nc)] = current
                queue.append((nr,nc))
    return None

def collision_free_pose(throat_width, pose):
    # Exact AABB check for the axis-aligned poses enumerated by this probe.
    cx, cy, yaw = pose
    assert yaw == 0
    if cx - CAR_LENGTH/2 < 0 or cx + CAR_LENGTH/2 > 24 or cy - CAR_WIDTH/2 < 0 or cy + CAR_WIDTH/2 > 10:
        return False
    overlaps_throat = cx + CAR_LENGTH/2 > 10 and cx - CAR_LENGTH/2 < 15
    return not overlaps_throat or abs(cy-5) + CAR_WIDTH/2 < throat_width/2

def run():
    begin = time.perf_counter()
    rows = []
    poses = {'upstream_center': (6., 5., 0.), 'inside_center': (12.5, 5., 0.), 'inside_offset': (12.5, 5.3, 0.)}
    for res in (.1, .05, .025):
        for width in (2.6, 3.2, 3.6, 4.2):
            free0, xs, ys = grid(width, res)
            connected0 = path_between(free0, xs, ys) is not None
            for label, pose in poses.items():
                collision_free = collision_free_pose(width, pose)
                free1, xs, ys = grid(width, res, pose)
                nominal_path = path_between(free1, xs, ys) if collision_free else None
                free2, xs, ys = grid(width, res, pose, ENVELOPE_PAD)
                envelope_path = path_between(free2, xs, ys) if collision_free else None
                rows.append({'resolution_m':res, 'throat_width_m':width, 'pose':label,
                             'static_collision_free':collision_free, 'connected_without_vehicle':connected0,
                             'nominal_connection':nominal_path is not None,
                             'conservative_envelope_connection':envelope_path is not None,
                             'nominal_grid_path_length_m': None if nominal_path is None else float(np.linalg.norm(np.diff(nominal_path,axis=0),axis=1).sum())})
    # Check that refined and coarse grids agree in this selected toy case set.
    a, b, c = rows[:12], rows[12:24], rows[24:]
    keys = ('static_collision_free','connected_without_vehicle','nominal_connection','conservative_envelope_connection')
    coarse_changes = [dict(throat_width_m=x['throat_width_m'],pose=x['pose'],
                           changed_fields=[k for k in keys if x[k] != y[k]])
                      for x,y in zip(a,b) if any(x[k] != y[k] for k in keys)]
    fine_changes = [dict(throat_width_m=x['throat_width_m'],pose=x['pose'],
                         changed_fields=[k for k in keys if x[k] != y[k]])
                    for x,y in zip(b,c) if any(x[k] != y[k] for k in keys)]
    with (OUT / 'connectivity_cases.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {'scope':'Static geometry and one OD connection only; no dynamic closed-loop test.',
               'case_count':len(rows),'unique_geometries':12,
               'coarse_to_medium_changes':coarse_changes,'medium_to_fine_changes':fine_changes,
               'interpretation':'A false grid-connectivity result is lack of certification, not proof of continuous-space infeasibility. The envelope is a sufficient conservative common-path test, not an exact robust test.',
               'vehicle_length_m':CAR_LENGTH,'vehicle_width_m':CAR_WIDTH,
               'pedestrian_effective_radius_m':EFFECTIVE_PED_RADIUS,
               'pose_position_bound_m':POSITION_ERROR,'pose_yaw_bound_deg':3,
               'conservative_envelope_padding_m':ENVELOPE_PAD,
               'straight_braking_example':{'initial_center_x_m':2.5,'initial_speed_mps':1.5,
                   'constant_deceleration_to_upstream_x6_mps2':1.5**2/(2*(6-2.5)),
                   'constant_deceleration_to_inside_x12_5_mps2':1.5**2/(2*(12.5-2.5)),
                   'limits':'Only a straight static road; no moving actors or steering uncertainty in the braking check.'},
               'elapsed_seconds':time.perf_counter()-begin}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), constrained_layout=True)
    for ax, label, title in zip(axes, ('inside_center','upstream_center'), ('A: Collision-free stop blocks the passage', 'B: Upstream stop preserves a passage')):
        width, pose = 2.6, poses[label]
        h = (10-width)/2
        for bottom in (0, 10-h):
            ax.add_patch(Rectangle((10,bottom),5,h,facecolor='#a2a9b2',edgecolor='#545d6a'))
        ax.add_patch(Rectangle((pose[0]-CAR_LENGTH/2,pose[1]-CAR_WIDTH/2),CAR_LENGTH,CAR_WIDTH,facecolor='#2563eb',alpha=.9))
        free, xs, ys = grid(width,.05,pose)
        path = path_between(free,xs,ys)
        if path is not None:
            ax.plot(path[:,0],path[:,1],color='#059669',lw=2.5,label='Pedestrian grid path')
        ax.scatter([1,23],[5,5],c=['#059669','#d97706'],s=50,zorder=5)
        ax.text(1,5.5,'Entry',ha='center',fontsize=9)
        ax.text(23,5.5,'Exit',ha='center',fontsize=9)
        ax.set(title=title,xlim=(0,24),ylim=(0,10),xlabel='x (m)',ylabel='y (m)')
        ax.set_aspect('equal')
        ax.grid(alpha=.15)
    fig.suptitle('Static feasibility probe - not a traffic simulation or planner benchmark',fontsize=12)
    fig.savefig(OUT / 'waiting_connectivity.png', dpi=170)
    plt.close(fig)
    print(json.dumps(summary, indent=2))
    for row in rows[:12]:
        print(row)

if __name__ == '__main__':
    run()
