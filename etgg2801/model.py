# FILENAME: model.py
# BY: Andrew Holbrook
# DATE: 9/24/2015

import ctypes
from OpenGL import GL
from . import GLWindow, Vector4, Matrix4

class Model(object):
    """Class for representing a Wavefront OBJ object.
    """
    def __init__(self):
        self.parts = []
        self.normals = []
        self.num_indices = 0
    
    def __str__(self):
        return str(self.num_indices)
    
    def getNumParts(self):
        return len(self.parts)
    
    def getNumIndices(self):
        return self.num_indices
    
    def getNumNormals(self):
        return len(self.normals)
    
    def getOBJVertexList(self):
        objVertexList = []
        for p in self.parts:
            objVertexList += p.vertices
        
        return objVertexList
    
    def getOBJUVList(self):
        objUVList = []
        for p in self.parts:
            objUVList += p.uvs
        
        return objUVList
    
    def getVertexList(self):
        vertexList = []
        
        objVertList = self.getOBJVertexList()
        for i in self.getIndexList():
            vertexList += objVertList[i * 3 : i * 3 + 3]
        
        return vertexList
    
    def getUVList(self):
        uvList = []
        
        objUVList = self.getOBJUVList()
        for i in self.getUVIndexList():
            uvList += objUVList[i * 2 : i * 2 + 2]
        
        return uvList
    
    def getIndexList(self):
        tmpList = []
        for p in self.parts:
            tmpList += p.indices
        
        return tmpList
    
    def getUVIndexList(self):
        tmpList = []
        for p in self.parts:
            tmpList += p.uvIndices
        
        return tmpList
    
    def getNormalList(self):
        return self.normals
    
    def generateNormals(self):
        vertexList = self.getVertexList()
        self.normals = []
        for i in range(0, len(vertexList), 9):
            v0 = Vector4(vertexList[i : i + 3])
            v1 = Vector4(vertexList[i + 3 : i + 6])
            v2 = Vector4(vertexList[i + 6 : i + 9])
            
            u = v1 - v0
            v = v2 - v1
            n = u.cross(v).normalize()
            
            self.normals += n.getXYZ() * 3
    
    def addPart(self, p):
        self.parts.append(p)
        self.num_indices += p.getNumIndices()
    
    def cleanup(self):
        GL.glDeleteBuffers(1, self.positionBuffer)
        GL.glDeleteBuffers(1, self.colorBuffer)
        GL.glDeleteBuffers(1, self.normalBuffer)
        GL.glDeleteBuffers(1, self.indexBuffer)
        GL.glDeleteVertexArrays(1, self.vertexArrayObject)
    
    def loadToVRAM(self):
        """Create the OpenGL objects for rendering this model.
        """
        
        # Create vertex array object to encapsulate the state needed to provide
        # vertex information.
        self.vertexArrayObject = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vertexArrayObject)
        
        # postition vertex buffer object
        self.positionBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.positionBuffer)
        
        # read and copy vertex data to VRAM
        vertexList = self.getVertexList()
        c_vertexArray = ctypes.c_float * len(vertexList)
        c_vertexArray = c_vertexArray(*vertexList)
        del vertexList
        
        GL.glBufferData(GL.GL_ARRAY_BUFFER, c_vertexArray, GL.GL_STATIC_DRAW)
        del c_vertexArray
        
        # position data is associated with location 0
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, 0, None)
        
        # color vertex buffer object
        self.uvBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.uvBuffer)
        
        uvList = self.getUVList()
        uv = ctypes.c_float * len(uvList)
        uv = uv(*uvList)
        del uvList
        
        GL.glBufferData(GL.GL_ARRAY_BUFFER, uv, GL.GL_STATIC_DRAW)
        del uv
        
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, False, 0, None)
        
        self.normalBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.normalBuffer)
        
        normalList = self.getNormalList()
        c_normals = ctypes.c_float * len(normalList)
        c_normals = c_normals(*normalList)
        del normalList
        
        GL.glBufferData(GL.GL_ARRAY_BUFFER, c_normals, GL.GL_STATIC_DRAW)
        del c_normals
        
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, False, 0, None)
        
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glEnableVertexAttribArray(2)
        
        GL.glBindVertexArray(0)
    
    def renderPartByIndex(self, index):
        GL.glBindVertexArray(self.vertexArrayObject)
        
        offset = 0
        for i in range(0, index):
            offset += self.parts[i].getNumIndices()
        
        c_offset = ctypes.c_void_p(offset * ctypes.sizeof(ctypes.c_uint))
        GL.glDrawElements(GL.GL_TRIANGLES, self.parts[index].getNumIndices(), GL.GL_UNSIGNED_INT, c_offset)
        
        GL.glBindVertexArray(0)
        
    def renderPartByName(self, name):
        GL.glBindVertexArray(self.vertexArrayObject)
        
        offset = 0
        for p in self.parts:
            if p.name == name:
                c_offset = ctypes.c_void_p(offset * ctypes.sizeof(ctypes.c_uint))
                GL.glDrawElements(GL.GL_TRIANGLES, p.getNumIndices(), GL.GL_UNSIGNED_INT, c_offset)
                break
            
            offset += p.getNumIndices()
        
        GL.glBindVertexArray(0)
    
    def renderAllParts(self):
        GL.glBindVertexArray(self.vertexArrayObject)
        
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.getNumIndices())
        
        GL.glBindVertexArray(0)

class ModelPart(object):
    """Represents a part (object) from the obj file.
    """
    def __init__(self):
        self.name = None
        self.vertices = []
        self.indices = []
        self.uvs = []
        self.uvIndices = []
    
    def getNumIndices(self):
        return len(self.indices)
    
    def getNumUVIndices(self):
        return len(self.uvIndices)
    
    def setName(self, name):
        self.name = name
    
    def addVertex(self, v):
        self.vertices.append(v)
    
    def addIndex(self, i):
        self.indices.append(i)
    
    def addUV(self, uv):
        self.uvs.append(uv)
    
    def addUVIndex(self, uvIndex):
        self.uvIndices.append(uvIndex)

class OBJReader(object):
    
    @staticmethod
    def readFile(file):
        """Reads an .obj file and returns the data as a Model object.
        """
        model = Model()
        currentPart = None
        
        fp = open(file)
        
        for line in fp:
            if line[0:2] == 'v ':
                verts = line.split()
                for i in range(1, len(verts)):
                    currentPart.addVertex(float(verts[i]))
            elif line[0:2] == 'vt':
                uvs = line.split()
                for i in range(1, len(uvs)):
                    currentPart.addUV(float(uvs[i]))
            elif line[0] == 'f':
                indices = line.split()
                for i in range(1, len(indices)):
                    tmpIndex = indices[i].split('/')
                    currentPart.addIndex(int(tmpIndex[0]) - 1)
                    if len(tmpIndex) > 1:
                        currentPart.addUVIndex(int(tmpIndex[1]) - 1)
            elif line[0] == 'o':
                if currentPart == None:
                    currentPart = ModelPart()
                else:
                    model.addPart(currentPart)
                    currentPart = ModelPart()
                
                currentPart.setName(line.split()[1])
                
        fp.close()
        
        if currentPart != None:
            model.addPart(currentPart)
        
        model.generateNormals()
        
        return model