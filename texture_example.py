import ctypes
import sdl2
from sdl2 import sdlimage
from math import *
import random
from OpenGL import GL
from etgg2801 import *

phong_vsrc = b'''
#version 400

layout (location = 0) in vec3 VertexPosition;
layout (location = 1) in vec2 UV;

out vec2 texCoord;
uniform mat4 modelview;
uniform mat4 projection;

void main()
{
    vec4 eyeVertex = modelview * vec4(VertexPosition, 1.0);
    texCoord = UV;
    gl_Position = projection * vec4(VertexPosition, 1.0);
}
'''

phong_fsrc = b'''
#version 400

in vec2 texCoord;

out vec4 FragColor;

uniform sampler2D sampler;

void main() {
    FragColor = texture(sampler, texCoord).rgba;
}
'''

class MyDelegate(GLWindowRenderDelegate):
    def __init__(self):
        super().__init__()
        
        self.initShaders()
        
        self.initUV()
        
        
        self.lightPosition = Vector4((0, 0.5, 5, 1.0))
        
        # location of model matrix in shader program
        self.modelview_loc = GL.glGetUniformLocation(self.shaderProgram, b"modelview");
        self.projection_loc = GL.glGetUniformLocation(self.shaderProgram, b"projection");
        self.sampler_loc = GL.glGetUniformLocation(self.shaderProgram, b"sampler")
        
        # set background color to black
        GL.glClearColor(0.0, 1.0, 0.0, 1.0)
        
        # enable face culling (backface by default)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        # (Rs Sr + Rd Dr, Gs Sg + Gd Dg, Bs Sb + Bd Db, As Sa + Ad Da)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        self.window = GLWindow.getInstance()
        
        self.initTexture()
        GL.glViewport(0, 0, window.size[0], window.size[1])
        
        self.scene = Scene()
    
    def initShaders(self):
        
        # build vertex shader object
        self.vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(self.vertexShader, phong_vsrc)
        GL.glCompileShader(self.vertexShader)
        result = GL.glGetShaderiv(self.vertexShader, GL.GL_COMPILE_STATUS)
        if result != 1:
            print(GL.glGetShaderInfoLog(self.vertexShader))
            raise Exception("Error compiling vertex shader")
        
        # build fragment shader object
        self.fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(self.fragmentShader, phong_fsrc)
        GL.glCompileShader(self.fragmentShader)
        result = GL.glGetShaderiv(self.fragmentShader, GL.GL_COMPILE_STATUS)
        if result != 1:
            print(GL.glGetShaderInfoLog(self.fragmentShader))
            raise Exception("Error compiling fragment shader")
        
        # build shader program and attach shader objects
        self.shaderProgram = GL.glCreateProgram()
        GL.glAttachShader(self.shaderProgram, self.vertexShader)
        GL.glAttachShader(self.shaderProgram, self.fragmentShader)
        GL.glLinkProgram(self.shaderProgram)
    
    def initUV(self):
        self.vertexArrayObject = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vertexArrayObject)
        
        # postition vertex buffer object
        self.positionBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.positionBuffer)
        
        verts = ctypes.c_float * (3 * 3)
        verts = verts(-0.5, -0.5, -1, 0.5, -0.5, -1, 0.5, 0.5, -1)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, verts, GL.GL_STATIC_DRAW)
        
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, 0, None)
        
        self.uvBuffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.uvBuffer)
        
        uv = ctypes.c_float * (2 * 3)
        uv = uv(0.0, 0.0, 1.0, 0.0, 1.0, 1.0)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, uv, GL.GL_STATIC_DRAW)
        
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, False, 0, None)
        
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        
        GL.glBindVertexArray(0)
    
    def initTexture(self):
        GL.glActiveTexture(GL.GL_TEXTURE0)
        self.textureObject = GL.glGenTextures(1)
        
        rockmanImage = sdlimage.IMG_Load(b'rockman.png')
        pixels = ctypes.cast(rockmanImage.contents.pixels, ctypes.c_void_p)
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureObject)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 128, 128, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pixels)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    
    def cleanup(self):
        self.scene.cleanup()
        GL.glDeleteTextures(1, self.textureObject)
        GL.glDeleteShader(self.vertexShader)
        GL.glDeleteShader(self.fragmentShader)
        GL.glDeleteProgram(self.shaderProgram)
    
    def update(self, dtime):
        self.scene.update(dtime)
    
    def render(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        GL.glUseProgram(self.shaderProgram)
        
        projMatrix = Matrix4.getOrthographic(near=1.0,far=10.0)
        projMatrix.set(0, 0, projMatrix.get(0, 0) * (self.window.size[1] / self.window.size[0]))
        GL.glUniformMatrix4fv(self.projection_loc, 1, False, projMatrix.getCType())
        
        GL.glUniform1i(self.sampler_loc, 0)
        
        GL.glBindVertexArray(self.vertexArrayObject)
        
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        
        self.scene.render()
        
        GL.glBindVertexArray(0)
        
        GL.glUseProgram(0)

class Scene(object):
    def __init__(self):
        self.objects = []
    
    def addObject(self, o):
        self.objects.append(o)
    
    def removeObject(self, o):
        self.objects.remove(o)
    
    def cleanup(self):
        for o in self.objects:
            o.cleanup()
    
    def update(self, dtime):
        for o in self.objects:
            o.update(dtime)
    
    def render(self):
        for o in self.objects:
            o.render()

window = GLWindow((800, 600))

window.setRenderDelegate(MyDelegate())

window.mainLoop()