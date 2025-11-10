import pygame
import time
import random
import math
from Storage import Store
from Mesh import MeshObject

pygame.init()
pygame.font.init()
DB = Store("settings.json")

def loadvar(name, default):
    val = DB.get(name)
    if val == None:
        DB.set(name, default)
        return(default)
    else:
        return(val)

#system variables
WIDTH = loadvar("width", 800)
HEIGHT = loadvar("height", 600)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3dEngine.py")
clock = pygame.time.Clock()
FPS = loadvar("fps", 40)
font = pygame.font.SysFont('Arial', 16)
renderlist = []
CLOSERANGE = max(loadvar("clipping plane", 0.2), 0.01)
renderrange = loadvar("rendering range", 150)
GOODLIGHTING = loadvar("beautiful lighting", 0)
fov = loadvar("fov", 70)
cache = None
polycache = []
uselighting = True
lightpos = None
lightstrength = None

HALFPI = math.pi / 2
HALFWIDTH = WIDTH / 2
HALFHEIGHT = HEIGHT / 2
FOCAL = WIDTH / (2 * math.tan(math.radians(fov / 2)))

append = renderlist.append
WIDTH_ = WIDTH
HEIGHT_ = HEIGHT
FOCAL_ = FOCAL

#game variables
x = 0
y = 0
z = 0
pitch = 0
direct = 0
SENSITIVITY = loadvar("look sensitivity", 0.3)
tick = 0

#debug variables
f = 0
lf = time.time()
fpstxt = font.render(f"{f} FPS", True, (255, 0, 0))
debugobj = 0

randlist = []
objlist = []

colourmap = [(125, 0, 0), (125, 0, 0), (125, 125, 125), (255, 0, 0), (255, 0, 0), (75, 75, 255)]

randlist.append(("light", (0, 0, 10), 75, (255, 255, 255)))
for i in range(2500):
    randx = random.randint(-100, 100)
    randy = random.randint(-100, 100)
    randz = random.randint(-10, 10)
    randlist.append(("poly", [(randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2))], 1, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

def inp():
    global x, y, z, direct, pitch, lightpos, lightstrength
    keypressed = pygame.key.get_pressed()
    speed = 0.6 if keypressed[pygame.K_LSHIFT] else 0.25

    if keypressed[pygame.K_RIGHT]:
        direct += 3
    if keypressed[pygame.K_LEFT]:
        direct -= 3

    # mouse: positive -> turn right (adjust sign if you prefer the opposite)
    mx, my = pygame.mouse.get_rel()
    direct += mx * -SENSITIVITY
    pitch += my * -SENSITIVITY
    pitch = max(-80, min(80, pitch))  # prevent flipping
    direct %= 360

    # movement input
    move = (keypressed[pygame.K_w] - keypressed[pygame.K_s])  # forward/back
    sidemove = (keypressed[pygame.K_d] - keypressed[pygame.K_a])  # right/left
    upmove = ((keypressed[pygame.K_e] or keypressed[pygame.K_SPACE]) - (keypressed[pygame.K_q] or min(pygame.key.get_mods() & pygame.KMOD_CTRL, 1)))

    dirrad = math.radians(direct)
    # forward vector and right vector in world coords (consistent with projection)
    fx, fy = math.cos(dirrad), math.sin(dirrad)
    rx, ry = math.cos(dirrad + HALFPI), math.sin(dirrad + HALFPI)

    x += (fx * sidemove + rx * move) * speed
    y += (fy * sidemove + ry * move) * speed
    z += upmove * speed

    if keypressed[pygame.K_LALT]:
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    elif keypressed[pygame.K_RALT]:
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        print(lightpos, lightstrength)

def project_point(px, py, pz, cam, dirrad, pitchrad, dirradcos, dirradsin, pitchradcos, pitchradsin):
    global fov
    cx, cy, cz, cdirect, cpitch = cam
    dx, dy, dz = px - cx, py - cy, pz - cz

    # horizontal rotation
    rx = dx * dirradcos - dy * dirradsin
    ry = dx * dirradsin + dy * dirradcos
    rz = dz

    # vertical rotation
    ry2 = ry * pitchradcos - rz * pitchradsin
    rz2 = ry * pitchradsin + rz * pitchradcos

    if ry2 <= CLOSERANGE:
        ry2 = CLOSERANGE

    sx = HALFWIDTH + (rx * ry2**-1) * FOCAL
    sy = HALFHEIGHT - (rz2 * ry2**-1) * FOCAL
    return sx, sy, ry2

def calcdisp(scene, camera, renderrange):
    global lightpos, lightstrength, uselighting
    cx, cy, cz, cdirect, cpitch = camera
    dirrad = math.radians(cdirect)
    pitchrad = math.radians(cpitch)
    dirradcos = math.cos(-dirrad)
    dirradsin = math.sin(-dirrad)
    pitchradcos = math.cos(-pitchrad)
    pitchradsin = math.sin(-pitchrad)
    renderlist = []

    for targ in scene:
        group = targ[0]
        color = targ[3]

        # polygon object
        if group == "poly":
            verts = targ[1]
            projected_points = []
            avgpos = (0, 0, 0)
            visible = False  # track if any vertex projects on-screen

            for vx, vy, vz in verts:
                if lightpos is not None:
                    if GOODLIGHTING == True:
                        avgpos = tuple(int(x + y) for x, y in zip(avgpos, (vx, vy, vz)))
                    else:
                        avgpos = (vx, vy, vz)
                dx, dy, dz = vx - cx, vy - cy, vz - cz
                dist = dx*dx + dy*dy + dz*dz
                if dist > renderrange**2:
                    continue
                result = project_point(vx, vy, vz, camera, dirrad, pitchrad, dirradcos, dirradsin, pitchradcos, pitchradsin)
                if not result:
                    continue
                sx, sy, ry = result
                projected_points.append((sx, sy))
                if 0 <= sx <= WIDTH and 0 <= sy <= HEIGHT:
                    visible = True

            # add polygon if any vertex is visible
            if len(projected_points) >= 3 and visible:
                avg_dist = dist / len(verts)
                if lightpos is not None:
                    avgpos = tuple(map(lambda x: x / len(verts), avgpos))
                    lightdist = (int(avgpos[0]) - int(lightpos[0]))**2 + (int(avgpos[1]) - int(lightpos[1]))**2 + (int(avgpos[2]) - int(lightpos[2]))**2
                    brightness = min(2, lightstrength**2 / lightdist if lightdist != 0 else 0.01)
                    color = (
                        min(color[0] * brightness, 255),
                        min(color[1] * brightness, 255),
                        min(color[2] * brightness, 255)
                    )
                renderlist.append(("poly", (avg_dist, (color, projected_points))))

        # regular point/square object
        else:
            if uselighting:
                if group == "light":
                    lightpos = targ[1]
                    lightstrength = targ[2]
            else:
                lightpos = None

            px, py, pz = targ[1]
            dx, dy, dz = px - cx, py - cy, pz - cz
            dist = dx*dx + dy*dy + dz*dz
            if dist > renderrange**2:
                continue
            result = project_point(px, py, pz, camera, dirrad, pitchrad, dirradcos, dirradsin, pitchradcos, pitchradsin)
            if not result:
                continue
            sx, sy, ry = result
            size = max(targ[2] / ry, 1)
            if 0 < sx < WIDTH and 0 < sy < HEIGHT:
                renderlist.append((None, (ry, (color, (sx - size/2, sy - size/2, size, size)))))

    return renderlist

running = True
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
while running:
    clock.tick(FPS)
    inp()
    renderrange = max(10, min(renderrange, 1000))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSLASH:
                uselighting = 1 - uselighting
            if pygame.key.get_mods() & pygame.K_LSHIFT:
                if event.key == pygame.K_EQUALS:
                    renderrange += 10
                elif event.key == pygame.K_MINUS:
                    renderrange -= 10
    
    SCREEN.fill((0, 0, 0))
    
    objlist = []
    world = randlist + objlist
    renderlist = calcdisp(world, (x, y, z, direct, pitch), renderrange)
    renderlist.sort(key=lambda x: x[1][0], reverse=True)
    debugobj = len(renderlist)
    for obj in renderlist:
        try:
            if obj[0] == None:
                pygame.draw.rect(SCREEN, *obj[1][1])
            elif obj[0] == "poly":
                pygame.draw.polygon(SCREEN, *obj[1][1])
        except Exception as e:
            print(e)
    
    f = f + 1
    if time.time() - lf >= 1:
        fpstxt = font.render(f"{f}/{FPS} FPS | {renderrange} renderrange | {debugobj} points", True, (255, 0, 0))
        lf = time.time()
        f = 0
    SCREEN.blit(fpstxt, (5, 5))
    pygame.display.flip()
pygame.mouse.set_visible(True)
pygame.quit()