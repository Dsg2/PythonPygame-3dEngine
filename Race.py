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

def loadvar(name, default):
    val = DB.get(name)
    if val == None:
        DB.set(name, default)
        return(default)
    else:
        return(val)

m = input("Host or join? (port 5667) (h/j): ")
if m == "h":
    NM = NetManager(("server", 4), ["pos", "dir", "name"])
    s = Server(loadvar("hosting IP", "0.0.0.0"), int(input("Hosting port (default 5667): ")))
    
    def getclients():
        with s.clients_lock:
            return dict(s.clients)
        
    def connectedids():
        clients = getclients()
        return list(clients.keys())

elif m == "j":
    NM = NetManager("client")
    if input("try join server? (y/n): ") == "y":
        s = Client(loadvar("Default server IP", "forums-achievement.gl.at.ply.gg"), loadvar("Default server port", 11802))
    else:
        s = Client(input("Enter IP: "), int(input("Enter Port: ")))

#system variables
WIDTH = loadvar("width", 800)
HEIGHT = loadvar("height", 600)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3dEngine.py")
clock = pygame.time.Clock()
FPS = loadvar("fps", 40)
font = pygame.font.SysFont('Arial', 16)
renderlist = []
CLOSERANGE = loadvar("clipping plane", 0.2)
renderrange = loadvar("rendering range", 150)
GOODLIGHTING = loadvar("beautiful lighting", 0)
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
turnfactor = 0
maxspeed = 0
maxturn = 0
maxturnfactor = 0
lastspeed = 0
lastsmooth = 0

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

quadsize = 20
QUAD = MeshObject([[(0, 0, 0), (quadsize, 0, 0), (0, -quadsize, 0)], [(quadsize, -quadsize, 0), (quadsize, 0, 0), (0, -quadsize, 0)]])

colourmap = [(125, 0, 0), (125, 0, 0), (125, 125, 125), (255, 0, 0), (255, 0, 0), (75, 75, 255)]
othercolourmap = [(0, 0, 125), (0, 0, 125), (125, 125, 125), (0, 0, 255), (0, 0, 255), (255, 75, 75)]

TILEDATA = [
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ,
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ,
]
TILEPOSDATA = None

randlist.append(("light", (0, 0, 10), 75, (255, 255, 255)))
#for i in range(500):
#    randx = random.randint(-1000, 1000)
#    randy = random.randint(-1000, 1000)
#    randz = random.randint(-10, 10)
#    randlist.append(("poly", [(randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2)), (randx + random.randint(-2, 2), randy + random.randint(-2, 2), randz + random.randint(-2, 2))], 1, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))

def plane(x, y, z, size, colour):
    planecache = []
    QUAD.position = (x, y, z)
    for tri in QUAD.get_world_tri():
        planecache.append(("poly", tri, 1, colour))
    return planecache

TILES = []

try:
    for i in range(50):
        for j in range(50):
            tile_type = TILEDATA[i][j]
            
            # Calculate world position for this tile
            world_x = (i - 25) * quadsize
            world_y = (j - 25) * quadsize
            
            # Store tile info: (x, y, size, type)
            TILES.append({
                'x': world_x,
                'y': world_y,
                'size': quadsize,
                'type': tile_type
            })
            
            # Generate color based on tile type
            if tile_type == 1:
                tilecolour = (random.randint(110, 140), random.randint(110, 140), random.randint(110, 140))
            elif tile_type == 2:
                tilecolour = (random.randint(0, 50), random.randint(240, 255), random.randint(0, 50))
            else:
                tilecolour = (random.randint(240, 255), random.randint(0, 50), random.randint(0, 50))
            
            # Generate the plane geometry
            plan = plane(world_x, world_y, -2, 10, tilecolour)
            for tri in plan:
                randlist.append(tri)
        
    # Add this global variable at the top with your other game variables
    last_tile_cache = None

    def get_tile_at_position(world_x, world_y, use_cache=True):
        """
        Returns the tile type at the given world coordinates using boundary checking.
        Uses a cache system to check the last tile and its neighbors first for better performance.
        
        Returns:
            0 = off-track (red)
            1 = track (gray)
            2 = special/finish line (green)
            None = out of bounds or no tile found
        """
        global last_tile_cache
        
        def check_tile(tile):
            """Helper function to check if position is within a tile's boundaries"""
            x_min = tile['x']
            x_max = tile['x'] + tile['size']
            y_min = tile['y'] - tile['size']
            y_max = tile['y']
            
            return x_min <= world_x < x_max and y_min <= world_y < y_max
        
        # Try cache first
        if use_cache and last_tile_cache is not None:
            # Check if still on the same tile
            if check_tile(last_tile_cache):
                return last_tile_cache['type']
            
            # Check the 8 neighboring tiles
            cache_x = last_tile_cache['x']
            cache_y = last_tile_cache['y']
            tile_size = last_tile_cache['size']
            
            # Define 8 neighbor offsets (including diagonals)
            neighbor_offsets = [
                (-tile_size, 0),      # left
                (tile_size, 0),       # right
                (0, -tile_size),      # down
                (0, tile_size),       # up
                (-tile_size, -tile_size),  # bottom-left
                (tile_size, -tile_size),   # bottom-right
                (-tile_size, tile_size),   # top-left
                (tile_size, tile_size)     # top-right
            ]
            
            # Check neighbors
            for dx, dy in neighbor_offsets:
                neighbor_x = cache_x + dx
                neighbor_y = cache_y + dy
                
                # Find the neighbor tile with matching position
                for tile in TILES:
                    if tile['x'] == neighbor_x and tile['y'] == neighbor_y:
                        if check_tile(tile):
                            last_tile_cache = tile
                            return tile['type']
                        break
        
        # If cache miss, search all tiles
        print("oh no")
        for tile in TILES:
            if check_tile(tile):
                last_tile_cache = tile
                return tile['type']
        
        # Not found on any tile
        last_tile_cache = None
        return None

    def get_tile_info_at_position(world_x, world_y):
        """
        Returns the full tile dictionary at the given position.
        Useful if you need more info than just the type.
        """
        for tile in TILES:
            x_min = tile['x']
            x_max = tile['x'] + tile['size']
            y_min = tile['y']
            y_max = tile['y'] + tile['size']
            
            if x_min <= world_x < x_max and y_min <= world_y < y_max:
                return tile
        
        return None

    def inp():
        global x, y, z, direct, pitch, lightpos, lightstrength, incar, carx, cary, carz, carspeed, turnfactor, carturn, cardirect, lastspeed, lastsmooth
        keypressed = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_rel()
        
        if incar:
            dirrad = math.radians(cardirect)
            move = (keypressed[pygame.K_w] - keypressed[pygame.K_s])  # forward/back
            fx, fy = math.cos(dirrad), math.sin(dirrad)
            rx, ry = math.cos(dirrad + math.pi/2), math.sin(dirrad + math.pi/2)
            
            turnfactor = (turnfactor + 0.02 * keypressed[pygame.K_LSHIFT]) / 1.05
            turn = (keypressed[pygame.K_d] - keypressed[pygame.K_a]) * 20
            carturn = (carturn + min(1, max((mx + turn) * -SENSITIVITY * 0.4 * (turnfactor * 1.3 + 1), -1)) * 0.3) / (1.03 + (abs(carspeed / 800)))
            carspeed = (carspeed + move) / 1.01 / (1 + turnfactor / 30)
            carx += (rx * carspeed + fx * (turnfactor) * carturn * 10) * 0.03
            cary += (ry * carspeed + fy * (turnfactor) * carturn * 10) * 0.03
            carturn = min(max(-5, carturn), 5)
            cardirect += carturn
            x = carx - (math.sin(-dirrad) * ((carspeed * 0.1 / (turnfactor + 1)) + 10) + fx * (turnfactor) * carturn * -2)
            y = cary - (math.cos(-dirrad) * ((carspeed * 0.1 / (turnfactor + 1)) + 10) + fy * (turnfactor) * carturn * -2)
            z = carz + 4
            direct = cardirect + carturn * 1
            pitch = ((lastsmooth / -2) + carspeed / 10) - 15
            lastsmooth = (lastsmooth + (lastspeed - carspeed)) / 1.05
            lastspeed = carspeed
            
        else:
            speed = 0.6 if keypressed[pygame.K_LSHIFT] else 0.25

            if keypressed[pygame.K_RIGHT]:
                direct += 3
            if keypressed[pygame.K_LEFT]:
                direct -= 3

            # mouse: positive -> turn right (adjust sign if you prefer the opposite)
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
            rx, ry = math.cos(dirrad + math.pi/2), math.sin(dirrad + math.pi/2)

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

    def dispui():
        global maxspeed, maxturn, carspeed, carturn, turnfactor, maxturnfactor
        if abs(carspeed) > maxspeed:
            maxspeed = abs(carspeed)
        if abs(carturn) > maxturn:
            maxturn = abs(carturn)
        if abs(turnfactor) > maxturnfactor:
            maxturnfactor = abs(turnfactor)
        pygame.draw.rect(SCREEN, (225, 255, 255), (0, HEIGHT - 100, 100, 100))
        pygame.draw.rect(SCREEN, (0, 255, 0), (0, HEIGHT - 100, 50, abs(((carspeed / maxspeed) if maxspeed != 0 else 0) * 100)))
        pygame.draw.rect(SCREEN, (255, 0, 0), (0, HEIGHT - 100, 10, abs(((turnfactor / maxturnfactor) if maxturnfactor != 0 else 0) * 100)))
        pygame.draw.rect(SCREEN, (0, 0, 255), (75 if carturn >= 0 else 75 - abs(((carturn / maxturn) if maxturn != 0 else 0) * 25), HEIGHT - 100, abs(((carturn / maxturn) if maxturn != 0 else 0) * 25), 100))

    def project_point(px, py, pz, cam):
        global fov
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

        if ry2 <= CLOSERANGE:
            ry2 = CLOSERANGE

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
                    dist_sum += math.sqrt(dist)
                    result = project_point(vx, vy, vz, camera)
                    if not result:
                        continue
                    sx, sy, ry = result
                    projected_points.append((sx, sy))
                    if 0 <= sx <= WIDTH and 0 <= sy <= HEIGHT:
                        visible = True

                # add polygon if any vertex is visible
                if len(projected_points) >= 3 and visible:
                    avg_dist = dist_sum / len(verts)
                    if lightpos is not None:
                        avgpos = tuple(map(lambda x: x / len(verts), avgpos))
                        lightdist = math.sqrt(
                            (int(avgpos[0]) - int(lightpos[0]))**2 +
                            (int(avgpos[1]) - int(lightpos[1]))**2 +
                            (int(avgpos[2]) - int(lightpos[2]))**2
                        )
                        brightness = min(2, lightstrength / lightdist if lightdist != 0 else 0.01)
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
        
        current_tile = get_tile_at_position(carx, cary)

        if current_tile == 0:
            # Off track - maybe slow down the car
            carspeed *= 0.95

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
        vehicle.rotation = (0, 0, cardirect - 90 + carturn * (1 + turnfactor * 3) * (carspeed / 10))
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
        dispui()
        pygame.display.flip()
    pygame.mouse.set_visible(True)
    if m == "h":
        s.stop()
    else:
        s.disconnect()
    pygame.quit()
except Exception as e:
    DB.set("ERRORLOG", str(e))
    if m == "h":
        s.stop()
    else:
        s.disconnect()
    pygame.quit()