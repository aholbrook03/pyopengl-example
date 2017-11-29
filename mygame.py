import ctypes
import sdl2
from math import *
import random
from OpenGL import GL
from etgg2801 import *

texture_phong_vsrc = b'''
#version 400

layout (location = 0) in vec3 VertexPosition;
layout (location = 1) in vec2 UV;
layout (location = 2) in vec3 VertexNormal;

out vec4 normal;
out vec2 texCoord;
out vec4 eyeVertex;
uniform mat4 modelview;
uniform mat4 projection;

void main()
{
    normal = normalize(modelview * vec4(VertexNormal, 0));
    texCoord = UV;
    eyeVertex = modelview * vec4(VertexPosition, 1.0);
    gl_Position = projection * eyeVertex;
}
'''

texture_phong_fsrc = b'''
#version 400

in vec4 normal;
in vec2 texCoord;
in vec4 eyeVertex;
out vec4 FragColor;

uniform mat4 modelview;
uniform sampler2D sampler;

void main() {
    vec4 lightPos = vec4(0, 0.5, 5, 1);
    vec4 lv = normalize(lightPos - eyeVertex);
    float dotp = max(dot(lv, normal), 0);
    vec4 c = texture(sampler, texCoord).rgba;
    FragColor = clamp(c * dotp, 0.0, 1.0);
}
'''

class MyDelegate(GLWindowRenderDelegate):
    def __init__(self):
        super().__init__()
        self.lightPosition = Vector4((0.0, 0.5, 3.0, 1.0))
        self.angle = 0
        self.dangle = 360.0 / 5000.0
        self.initShaders()
        self.initTexture()
        
        # location of model and projection matrices in shader program
        self.modelview_loc = GL.glGetUniformLocation(self.shaderProgram, b"modelview")
        self.projection_loc = GL.glGetUniformLocation(self.shaderProgram, b"projection")
        
        # location of sampler in shader program
        self.sampler_loc = GL.glGetUniformLocation(self.shaderProgram, b"sampler")
        
        # set background color to black
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        
        # enable depth testing
        GL.glEnable(GL.GL_DEPTH_TEST)
        
        self.window = GLWindow.getInstance()
        GL.glViewport(0, 0, window.size[0], window.size[1])
        
        self.scene = Scene()
    
    def initShaders(self):
        
        # build vertex shader object
        self.vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(self.vertexShader, texture_phong_vsrc)
        GL.glCompileShader(self.vertexShader)
        result = GL.glGetShaderiv(self.vertexShader, GL.GL_COMPILE_STATUS)
        if result != 1:
            print(GL.glGetShaderInfoLog(self.vertexShader))
            raise Exception("Error compiling vertex shader")
        
        # build fragment shader object
        self.fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(self.fragmentShader, texture_phong_fsrc)
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
        
    def initTexture(self):
        GL.glActiveTexture(GL.GL_TEXTURE0)
        self.textureObject = GL.glGenTextures(1)
        
        boatDiffuse = sdlimage.IMG_Load(b'/Users/andrewholbrook/Desktop/boat_OBJ/master_diffuse.png')
        pixels = ctypes.cast(boatDiffuse.contents.pixels, ctypes.c_void_p)
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureObject)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 2048, 2048, 0, GL.GL_BGRA, GL.GL_UNSIGNED_BYTE, pixels)
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
        
    def cleanup(self):
        self.scene.cleanup()
        GL.glDeleteShader(self.vertexShader)
        GL.glDeleteShader(self.fragmentShader)
        GL.glDeleteProgram(self.shaderProgram)
    
    def update(self, dtime):
        self.angle += self.dangle * dtime
        if self.angle >= 360:
            self.angle -= 360
        self.scene.update(dtime)
    
    def render(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        GL.glUseProgram(self.shaderProgram)
        
        projMatrix = Matrix4.getOrthographic(near=1,far=50)
        projMatrix.set(0, 0, projMatrix.get(0, 0) * (self.window.size[1] / self.window.size[0]))
        GL.glUniformMatrix4fv(self.projection_loc, 1, False, projMatrix.getCType())
        
        boatPosition = Vector4((0, 0, -10, 1))
        mvMatrix = Matrix4.getTranslation(*boatPosition.getXYZ())
        
        cameraPosition = Vector4((0, 5, -4, 1))
        cameraMatrix = Matrix4.getTranslation(*cameraPosition.getXYZ())
        cameraMatrix = Matrix4.getTranslation(*(boatPosition * -1).getXYZ()) * cameraMatrix
        cameraMatrix = Matrix4.getRotation(ay=self.angle) * cameraMatrix
        cameraMatrix = Matrix4.getTranslation(*boatPosition.getXYZ()) * cameraMatrix
        
        lookAt = cameraMatrix.position() - boatPosition
        lookAt.normalize()
        
        worldUp = Vector4((0, 1, 0, 0))
        left = worldUp.cross(lookAt)
        left.normalize()
        
        up = lookAt.cross(left)
        up.normalize()
        
        cameraMatrix.setOrientation(left, up, lookAt)
        
        
        mvMatrix = cameraMatrix.inverse() * mvMatrix
        
        GL.glUniformMatrix4fv(self.modelview_loc, 1, False, mvMatrix.getCType())
        
        GL.glUniform1i(self.sampler_loc, 0)
        boat.renderAllParts()
        
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
        #sl = GLWindow.getInstance().renderDelegate.shininess_loc
        #GL.glUniform1f(sl, ctypes.c_float(50.0))
        for o in self.objects:
            o.render()

window = GLWindow((800, 600))
window.setRenderDelegate(MyDelegate())

boat = OBJReader.readFile('/Users/andrewholbrook/Desktop/boat_OBJ/boat.obj')
boat.loadToVRAM()

window.mainLoop()