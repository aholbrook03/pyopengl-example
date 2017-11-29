# FILENAME: matmath.py
# BY: Andrew Holbrook
# DATE: 9/24/2016

from ctypes import c_float
from math import cos, sin, radians

class Matrix4(object):
    
    @staticmethod
    def getIdentity():
        return Matrix4()
    
    @staticmethod
    def getRotation(ax=0.0, ay=0.0, az=0.0):
        caz = cos(radians(az))
        saz = sin(radians(az))
        zm = Matrix4(((caz, -saz, 0, 0), (saz, caz, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
        
        cay = cos(radians(ay))
        say = sin(radians(ay))
        ym = Matrix4(((cay, 0, say, 0), (0, 1, 0, 0), (-say, 0, cay, 0), (0, 0, 0, 1)))
        
        cax = cos(radians(ax))
        sax = sin(radians(ax))
        xm = Matrix4(((1, 0, 0, 0), (0, cax, -sax, 0), (0, sax, cax, 0), (0, 0, 0, 1)))
        
        return xm * ym * zm
    
    @staticmethod
    def getTranslation(dx=0.0, dy=0.0, dz=0.0):
        return Matrix4(((1, 0, 0, dx), (0, 1, 0, dy), (0, 0, 1, dz), (0, 0, 0, 1)))
    
    @staticmethod
    def getScale(sx=1.0, sy=1.0, sz=1.0):
        return Matrix4(((sx, 0, 0, 0), (0, sy, 0, 0), (0, 0, sz, 0), (0, 0, 0, 1)))
    
    @staticmethod
    def getOrthographic(top=1, bottom=-1, left=-1, right=1, near=1, far=2):
        a = 2 / (right - left)
        b = (right + left) / (right - left)
        c = 2 / (top - bottom)
        d = (top + bottom) / (top - bottom)
        e = 2 / (far - near)
        f = (far + near) / (far - near)
        
        return Matrix4(((a, 0, 0, -b), (0, c, 0, -d), (0, 0, -e, -f), (0, 0, 0, 1)))
    
    def __init__(self, data=None):
        if not data:
            self.data = [[0] * i + [1] + [0] * (3 - i) for i in range(4)]
        elif isinstance(data, tuple) or isinstance(data, list):
            if len(data) == 4:
                self.data = [list(row) for row in data]
            elif len(data) == 3:
                self.data = [list(row) for row in data]
                self.data[0] += [0]
                self.data[1] += [0]
                self.data[2] += [0]
                self.data.append([0, 0, 0, 1])
    
    def __str__(self):
        tmpstr = ''
        for row in self.data:
            tmpstr += str(row) + '\n'
        
        return tmpstr
    
    def get(self, row, col):
        return self.data[row][col]
    
    def set(self, row, col, value):
        self.data[row][col] = value
    
    def setColumn(self, col, v):
        for idx in range(3):
            self.data[idx][col] = v.data[idx]
    
    def setPosition(self, pos):
        self.setColumn(3, pos)
    
    def setOrientation(self, x, y, z):
        self.setColumn(0, x)
        self.setColumn(1, y)
        self.setColumn(2, z)
    
    def rotation(self):
        return Matrix4([[self.data[j][i] for i in range(3)] for j in range(3)])
    
    def inverseRotation(self):
        return Matrix4([[self.data[i][j] for i in range(3)] for j in range(3)])
    
    def position(self):
        return Vector4([self.data[i][3] for i in range(3)])
    
    def inverse(self):
        invRot = self.inverseRotation()
        pos = (invRot * self.position()) * -1
        invRot.setPosition(pos)
        
        return invRot
    
    def getCType(self):
        """Returns a ctypes-compatible array representing this matrix.
        """
        tmparray = (c_float * 16)()
        for i in range(16):
            tmparray[i] = self.data[i % 4][i // 4]
        
        return tmparray
    
    def __add__(self, other):
        return Matrix4([[self.data[i][j] + other.data[i][j] for j in range(4)] for i in range(4)])
    
    def __sub__(self, other):
        return Matrix4([[self.data[i][j] - other.data[i][j] for j in range(4)] for i in range(4)])
    
    def __mul__(self, other):
        if isinstance(other, Vector4):
            return Vector4([sum([self.data[j][i] * other.data[i] for i in range(4)]) for j in range(4)])
        elif isinstance(other, Matrix4):
            return Matrix4([[sum([self.data[k][j] * other.data[j][i] for j in range(4)]) for i in range(4)] for k in range(4)])

class Vector4(object):
    def __init__(self, data=None):
        if not data:
            self.data = [0.0, 0.0, 0.0, 1.0]
        elif isinstance(data, tuple) or isinstance(data, list):
            self.data = list(data) + [1,] * (4 - len(data))
    
    def __str__(self):
        return str(self.data)
    
    def __add__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector4([self.data[i] + other for i in range(4)])
        elif isinstance(other, Vector4):  
            return Vector4([self.data[i] + other.data[i] for i in range(4)])
    
    def __sub__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector4([self.data[i] - other for i in range(4)])
        elif isinstance(other, Vector4):  
            return Vector4([self.data[i] - other.data[i] for i in range(4)])
    
    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector4([self.data[i] * other for i in range(4)])
        elif isinstance(other, Vector4):
            return sum([self.data[i] * other.data[i] for i in range(4)])
    
    def dot(self, other):
        if isinstance(other, Vector4):
            return self.getX() * other.getX() + self.getY() * other.getY() + self.getZ() * other.getZ()
    
    def cross(self, other):
        if isinstance(other, Vector4):
            x = self.getY() * other.getZ() - self.getZ() * other.getY()
            y = self.getZ() * other.getX() - self.getX() * other.getZ()
            z = self.getX() * other.getY() - self.getY() * other.getX()
            return Vector4((x, y, z, 0.0))
    
    def length2(self):
        return self.getX() ** 2 + self.getY() ** 2 + self.getZ() ** 2
    
    def length(self):
        return self.length2() ** 0.5
    
    def normalize(self):
        tmplen = self.length2()
        if tmplen != 0:
            tmplen = 1.0 / tmplen ** 0.5
            self.data[0] *= tmplen
            self.data[1] *= tmplen
            self.data[2] *= tmplen
        
        return self
    
    def getCType(self):
        """Returns a ctypes-compatible array representing this Vector4.
        """
        tmparray = (c_float * 4)()
        for i in range(4):
            tmparray[i] = self.data[i]
        
        return tmparray
    
    def getXYZ(self):
        return self.data[0:-1]
    
    def getX(self):
        return self.data[0]
    
    def getY(self):
        return self.data[1]
    
    def getZ(self):
        return self.data[2]
    
    def getW(self):
        return self.data[3]
    
    def setX(self, x):
        self.data[0] = x
    
    def setY(self, y):
        self.data[1] = y
    
    def setZ(self, z):
        self.data[2] = z
    
    def setW(self, w):
        self.data[3] = w