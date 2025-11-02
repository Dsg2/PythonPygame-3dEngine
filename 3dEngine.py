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

#game variables
x = 0
y = 0
direct = 0
fov = loadvar("fov", 70)
SENSITIVITY = loadvar("look sensitivity", 0.3)

#debug variables
f = 0
lf = time.time()
fpstxt = font.render(f"{f} FPS", True, (255, 0, 0))
debugobj = 0

randlist = []
for i in range(1500):
    randlist.append(((random.randint(-100, 100), random.randint(-100, 100), random.randint(-10, 10)), random.randint(100, 400), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

def inp():
    global x, y, direct
    keypressed = pygame.key.get_pressed()
    if keypressed[pygame.K_LSHIFT]:
        speed = 0.6
    else:
        speed = 0.25
    if keypressed[pygame.K_RIGHT]:
        direct += 3
    if keypressed[pygame.K_LEFT]:
        direct -= 3
    direct += (pygame.mouse.get_rel()[0]) * SENSITIVITY
    move = (keypressed[pygame.K_w] - keypressed[pygame.K_s])
    sidemove = (keypressed[pygame.K_d] - keypressed[pygame.K_a])
    dirrad = math.radians(direct)
    sidedirrad = math.radians(direct + 90)
    x += math.cos(dirrad) * move * speed + math.cos(sidedirrad) * sidemove * speed
    y += math.sin(dirrad) * move * speed + math.sin(sidedirrad) * sidemove * speed
    direct %= 360
    if keypressed[pygame.K_LALT]:
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    elif keypressed[pygame.K_RALT]:
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

def calcdisp(scene, camera, renderrange):
    x, y, direct = camera
    renderlist = []
    for targ in scene:
        dist = max(((x - targ[0][0])**2 + (y - targ[0][1])**2)**0.5, 0.01)
        if dist < renderrange:
            dire = (math.degrees(math.atan2(targ[0][1] - y, targ[0][0] - x)) - direct) % 360
            dirrad = math.radians(dire)
            targx = math.sin(dirrad) * dist
            targy = math.cos(dirrad) * dist * -1
            if targy < 0:
                if (dire <= fov / 2 or dire >= 360 - fov / 2):
                    dispdire = (dire - 360) if dire > 180 else dire
                    dispx = math.sin(math.radians(dispdire))
                    if dist > 0:
                        size = (targ[1] / dist) if (targ[1] / dist) > 1 else 1
                    else:
                        size = 1
                    if size > 1:
                        renderlist.append((dist, (targ[2], (round(((dispx + 1) / 2) * WIDTH + (size / -2)), round(HEIGHT / 2 + (size / -2)), round(size), round(size)))))
    return(renderlist)
    
running = True
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
while running:
    clock.tick(FPS)
    inp()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    SCREEN.fill((0, 0, 0))    
    
    renderlist = calcdisp(randlist, (x, y, direct), renderrange)
    renderlist.sort(key=lambda x: x[0], reverse=True)
    debugobj = len(renderlist)
    for obj in renderlist:
        try:
            pygame.draw.rect(SCREEN, *obj[1])
        except Exception as e:
            print(e)
    
    f = f + 1
    if time.time() - lf >= 1:
        fpstxt = font.render(f"{f} FPS | {debugobj} objects", True, (255, 0, 0))
        lf = time.time()
        f = 0
    SCREEN.blit(fpstxt, (5, 5))
    pygame.display.flip()
pygame.mouse.set_visible(True)
pygame.quit()