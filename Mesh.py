import math

class MeshObject:
    def __init__(self, triangles, position=(0,0,0), rotation=(0,0,0)):
        """
        triangles: list of triangles, each triangle is [(x,y,z), (x,y,z), (x,y,z)]
        position: (x, y, z) world coordinates
        rotation: (rx, ry, rz) in degrees
        """
        self.local_triangles = triangles  # local coords
        self.position = position
        self.rotation = rotation  # rotation around (x,y,z) in degrees

    def move(self, dx=0, dy=0, dz=0):
        x, y, z = self.position
        self.position = (x + dx, y + dy, z + dz)

    def rotate(self, rx=0, ry=0, rz=0):
        rx0, ry0, rz0 = self.rotation
        self.rotation = (rx0 + rx, ry0 + ry, rz0 + rz)

    def get_world_tri(self):
        """Return triangles transformed to world coordinates"""
        rx, ry, rz = map(math.radians, self.rotation)
        sx, sy, sz = self.position
        world_tris = []
        for tri in self.local_triangles:
            transformed = []
            for x, y, z in tri:
                # Rotate around X
                y, z = y*math.cos(rx) - z*math.sin(rx), y*math.sin(rx) + z*math.cos(rx)
                # Rotate around Y
                x, z = x*math.cos(ry) + z*math.sin(ry), -x*math.sin(ry) + z*math.cos(ry)
                # Rotate around Z
                x, y = x*math.cos(rz) - y*math.sin(rz), x*math.sin(rz) + y*math.cos(rz)
                # Translate
                x, y, z = x + sx, y + sy, z + sz
                transformed.append((x, y, z))
            world_tris.append(transformed)
        return world_tris