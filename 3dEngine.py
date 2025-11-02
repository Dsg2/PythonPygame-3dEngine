import pygame
import time
import random
import math
from Storage import Store

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
renderrange = loadvar("rendering range", 150)
cache = None
polycache = []
uselighting = True
lightpos = None
lightstrength = None

#game variables
x = 0
y = 0
z = 0
direct = 0
fov = loadvar("fov", 70)
SENSITIVITY = loadvar("look sensitivity", 0.3)

#debug variables
f = 0
lf = time.time()
fpstxt = font.render(f"{f} FPS", True, (255, 0, 0))
debugobj = 0

randlist = []
#(group, (x, y, z), size, (r, g, b))
#for i in range(15000):
#    randlist.append((None, (random.randint(-100, 100), random.randint(-100, 100), random.randint(-10, 10)), random.randint(100, 400), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

randlist.append(("light", (0, 0, 0), 10, (255, 255, 255)))
for i in range(1500):
    randx = random.randint(-100, 100)
    randy = random.randint(-100, 100)
    randz = random.randint(-10, 10)
    randlist.append(("poly", [(randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2))], 1, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))
randlist.append((None, (-5, 0, 0), 100, (0, 0, 255)))

def inp():
    global x, y, direct, lightpos, lightstrength
    keypressed = pygame.key.get_pressed()
    speed = 0.6 if keypressed[pygame.K_LSHIFT] else 0.25

    if keypressed[pygame.K_RIGHT]:
        direct += 3
    if keypressed[pygame.K_LEFT]:
        direct -= 3

    # mouse: positive -> turn right (adjust sign if you prefer the opposite)
    direct += pygame.mouse.get_rel()[0] * -SENSITIVITY
    direct %= 360

    # movement input
    move = (keypressed[pygame.K_w] - keypressed[pygame.K_s])  # forward/back
    sidemove = (keypressed[pygame.K_d] - keypressed[pygame.K_a])  # right/left

    dirrad = math.radians(direct)
    # forward vector and right vector in world coords (consistent with projection)
    fx, fy = math.cos(dirrad), math.sin(dirrad)
    rx, ry = math.cos(dirrad + math.pi/2), math.sin(dirrad + math.pi/2)

    x += (fx * sidemove + rx * move) * speed
    y += (fy * sidemove + ry * move) * speed

    if keypressed[pygame.K_LALT]:
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    elif keypressed[pygame.K_RALT]:
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        print(lightpos, lightstrength)

def project_point(px, py, pz, cam):
    cx, cy, cz, cdirect = cam
    dx, dy, dz = px - cx, py - cy, pz - cz
    dirrad = math.radians(cdirect)
    rx = dx * math.cos(-dirrad) - dy * math.sin(-dirrad)
    ry = dx * math.sin(-dirrad) + dy * math.cos(-dirrad)
    # Early reject: behind camera or too close
    if ry <= 0.2:
        return None
    # Projection
    focal = WIDTH / (2 * math.tan(math.radians(fov / 2)))
    sx = WIDTH / 2 + (rx / ry) * focal
    sy = HEIGHT / 2 - (dz / ry) * focal
    return sx, sy, ry

def calcdisp(scene, camera, renderrange):
    global lightpos, lightstrength, uselighting
    cx, cy, cz, cdirect = camera
    renderlist = []

    for targ in scene:
        group = targ[0]
        color = targ[3]

        # polygon object
        if group == "poly":
            verts = targ[1]
            dist_sum = 0
            projected_points = []
            avgpos = (0, 0, 0)

            for vx, vy, vz in verts:
                if lightpos != None:
                    avgpos = tuple(x + y for x, y in zip(avgpos, (vx, vy, vz)))
                dx, dy, dz = vx - cx, vy - cy, vz - cz
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                dist_sum += dist
                if dist > renderrange:
                    break
                result = project_point(vx, vy, vz, camera)
                if not result:
                    break
                sx, sy, ry = result
                projected_points.append((sx, sy))
            else:
                # Only add if all vertices were projected successfully
                avg_dist = dist_sum / len(verts)
                if lightpos != None:
                    avgpos = tuple(map(lambda x: x / len(verts), avgpos))
                    lightdist = math.sqrt((avgpos[0] - lightpos[0])**2 + (avgpos[1] - lightpos[1])**2 + (avgpos[2] - lightpos[2])**2)
                    brightness = min(1, lightstrength / lightdist if lightdist != 0 else 0.01)
                    color = (color[0] * brightness, color[1] * brightness, color[2] * brightness)
                renderlist.append(("poly", (avg_dist, (color, projected_points))))

        # regular point/square object
        else:
            if uselighting == True:
                if group == "light":
                    lightpos = targ[1]
                    lightstrength = targ[2]
            else:
                lightpos = None
            px, py, pz = targ[1]
            dx, dy, dz = px - cx, py - cy, pz - cz
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist > renderrange:
                continue
            result = project_point(px, py, pz, camera)
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
    
    renderlist = calcdisp(randlist, (x, y, z, direct), renderrange)
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
        fpstxt = font.render(f"{f}/{FPS} FPS | {renderrange} renderrange | {debugobj} objects", True, (255, 0, 0))
        lf = time.time()
        f = 0
    SCREEN.blit(fpstxt, (5, 5))
    pygame.display.flip()
pygame.mouse.set_visible(True)
pygame.quit()