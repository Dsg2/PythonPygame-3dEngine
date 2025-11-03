import pygame
import time
import random
import sys
import math
import socket
import json
from Storage import Store
from Mesh import MeshObject
from GameBarelib import Server, Client
from NetManager import NetManager

pygame.init()
pygame.font.init()
DB = Store("settings.json")

m = input("Host or join? (h/j): ")
if m == "h":
    NM = NetManager(("server", 4), ["pos", "dir", "name"])
    s = Server()
    
    def getclients():
        with s.clients_lock:
            return dict(s.clients)
        
    def connectedids():
        clients = getclients()
        return list(clients.keys())

elif m == "j":
    NM = NetManager("client")
    if input("try join server? (y/n): ") == "y":
        s = Client("leading-hon.gl.at.ply.gg", 57676)
    else:
        s = Client(input("Enter IP: "), 5667)

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
pitch = 0
direct = 0
fov = loadvar("fov", 70)
SENSITIVITY = loadvar("look sensitivity", 0.3)
tick = 0
incar = False

carx = 0
cary = 0
carz = 0
carspeed = 0
carturn = 0
cardirect = 0

#debug variables
f = 0
lf = time.time()
fpstxt = font.render(f"{f} FPS", True, (255, 0, 0))
debugobj = 0

randlist = []
objlist = []

vehicle = MeshObject([
    [(2.0, 2.0, 0.0), (3.0, 1.0, 1.5), (3.0, -1.0, 1.5)],
    [(2.0, 2.0, 0.0), (2.0, -2.0, 0.0), (3.0, -1.0, 1.5)],
    [(2.0, -2.0, 0.0), (-6.0, 0.0, 0.0), (2.0, 2.0, 0.0)],
    [(-6.0, 0.0, 0.0), (2.0, 2.0, 0.0), (3.0, 1.0, 1.5)],
    [(3.0, -1.0, 1.5), (2.0, -2.0, 0.0), (-6.0, 0.0, 0.0)],
    [(3.0, 1.0, 1.5), (3.0, -1.0, 1.5), (-6.0, 0.0, 0.0)],
])

colourmap = [(125, 0, 0), (125, 0, 0), (125, 125, 125), (255, 0, 0), (255, 0, 0), (75, 75, 255)]
othercolourmap = [(0, 0, 125), (0, 0, 125), (125, 125, 125), (0, 0, 255), (0, 0, 255), (255, 75, 75)]

randlist.append(("light", (0, 0, 0), 750, (255, 255, 255)))
for i in range(500):
    randx = random.randint(-1000, 1000)
    randy = random.randint(-1000, 1000)
    randz = random.randint(-10, 10)
    randlist.append(("poly", [(randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2))], 1, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

def inp():
    global x, y, z, direct, pitch, lightpos, lightstrength, incar, carx, cary, carz, carspeed, carturn, cardirect
    keypressed = pygame.key.get_pressed()
    mx, my = pygame.mouse.get_rel()
    
    if incar:
        dirrad = math.radians(cardirect)
        move = (keypressed[pygame.K_w] - keypressed[pygame.K_s])  # forward/back
        rx, ry = math.cos(dirrad + math.pi/2), math.sin(dirrad + math.pi/2)
        
        carspeed = (carspeed + move) / 1.01
        carx += (rx * carspeed) * 0.03
        cary += (ry * carspeed) * 0.03
        turn = (keypressed[pygame.K_d] - keypressed[pygame.K_a]) * 5
        carturn = (carturn + min(1, max((mx + turn) * -SENSITIVITY * 0.7, -1)) * 0.3) / (1.03 + (abs(carspeed / 800)))
        cardirect += carturn
        x = carx - (math.sin(-dirrad) * ((carspeed * 0.1) + 10))
        y = cary - (math.cos(-dirrad) * ((carspeed * 0.1) + 10))
        z = carz + 4
        direct = cardirect
        
    else:
        speed = 0.6 if keypressed[pygame.K_LSHIFT] else 0.25

        if keypressed[pygame.K_RIGHT]:
            direct += 3
        if keypressed[pygame.K_LEFT]:
            direct -= 3

        # mouse: positive -> turn right (adjust sign if you prefer the opposite)
        direct += mx * -SENSITIVITY
        pitch += my * -SENSITIVITY
        pitch = max(-89, min(89, pitch))  # prevent flipping
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
    cx, cy, cz, cdirect, cpitch = cam
    dx, dy, dz = px - cx, py - cy, pz - cz

    dirrad = math.radians(cdirect)
    pitchrad = math.radians(cpitch)

    # horizontal rotation
    rx = dx * math.cos(-dirrad) - dy * math.sin(-dirrad)
    ry = dx * math.sin(-dirrad) + dy * math.cos(-dirrad)
    rz = dz

    # vertical rotation
    ry2 = ry * math.cos(-pitchrad) - rz * math.sin(-pitchrad)
    rz2 = ry * math.sin(-pitchrad) + rz * math.cos(-pitchrad)

    if ry2 <= 0.2:
        return None

    focal = WIDTH / (2 * math.tan(math.radians(fov / 2)))
    sx = WIDTH / 2 + (rx / ry2) * focal
    sy = HEIGHT / 2 - (rz2 / ry2) * focal
    return sx, sy, ry2

def calcdisp(scene, camera, renderrange):
    global lightpos, lightstrength, uselighting
    cx, cy, cz, cdirect, cpitch = camera
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
                dist = dx*dx + dy*dy + dz*dz
                if dist > renderrange**2:
                    break
                dist_sum += math.sqrt(dist)
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

if m == "h":
    s.start()
    clients = [-1, -1, -1, -1]
    pcache = 0
else:
    s.connect()
    sid = -1

sendtick = 0
    
running = True
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
while running:
    clock.tick(FPS)
    
    msg = s.receive()
    if m == "h":
        pcache = 0
        NM.load(connectedids())
        if msg:
            client_id, text = msg
            if text is not None:
                NM.recv(text, client_id)
                #print(f"Client {client_id} sent: {text}")
            else:
                print(f"Client {client_id} disconnected")
        #print(carx, cary, carz, cardirect)
        sendtick += 1
        if sendtick > round(FPS / 24):
            sendtick = 0
            s.send(*NM.send(69, "pos", (round(carx, 2), round(cary, 2), round(carz, 2))))
            s.send(*NM.send(69, "dir", round(cardirect - 90 + carturn * (carspeed / 10), 2)))
    elif m == "j":
        if sid == -1:
            s.send("reqsid")
        if msg:
            if msg is None:
                print("disconnected")
            NM.recv(msg)
            #print(f"from server: {msg}")
        #print(carx, cary, carz, cardirect)
        sendtick += 1
        if sendtick > round(FPS / 24):
            sendtick = 0
            s.send(NM.send(sid, "pos", (round(carx, 2), round(cary, 2), round(carz, 2))))
            s.send(NM.send(sid, "dir", round(cardirect - 90 + carturn * (carspeed / 10), 2)))
    data = NM.data
    for event in data["syncqueue"]:
        print(event)
        if event[0] != "setsid":
            s.send(*event)
        else:
            sid = int(event[1])
    data["syncqueue"] = []
    NM.sync(data)
    
    objlist = []
    
    for client in data["clients"]:
        #print(data)
        if "pos" in data["clients"][client]:
            vehicle.position = tuple(map(float, data["clients"][client]["pos"]))
        if "dir" in data["clients"][client]:
            vehicle.rotation = (0, 0, float(data["clients"][client]["dir"]))
        for ind, tri in enumerate(vehicle.get_world_tri()):
            objlist.append(("poly", tri, 1, othercolourmap[ind]))
    
    inp()
    
    renderrange = max(10, min(renderrange, 1000))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSLASH:
                uselighting = 1 - uselighting
            elif event.key == pygame.K_TAB:
                incar = 1 - incar
            if pygame.key.get_mods() & pygame.K_LSHIFT:
                if event.key == pygame.K_EQUALS:
                    renderrange += 10
                elif event.key == pygame.K_MINUS:
                    renderrange -= 10
    
    tick = tick + 0.01
    tick = tick % 360
    
    SCREEN.fill((0, 0, 0))
    
    vehicle.position = (carx, cary, carz)
    vehicle.rotation = (0, 0, cardirect - 90 + carturn * (carspeed / 10))
    for ind, tri in enumerate(vehicle.get_world_tri()):
        objlist.append(("poly", tri, 1, colourmap[ind]))
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
        fpstxt = font.render(f"{f}/{FPS} FPS | {renderrange} renderrange | {debugobj} objects", True, (255, 0, 0))
        lf = time.time()
        f = 0
    SCREEN.blit(fpstxt, (5, 5))
    pygame.display.flip()
pygame.mouse.set_visible(True)
if m == "h":
    s.stop()
else:
    s.disconnect()
pygame.quit()