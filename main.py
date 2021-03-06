#!/usr/bin/python3

from re import M
from pygame.locals import *
from operator import add, sub
import pygame
import sys
import math
import random
import numpy as np

pygame.init()

# -----Options-----
WINDOW_SIZE = (1200, 800) # Width x Height in pixels
NUM_RAYS = 150 # Must be between 1 and 360
SOLID_RAYS = False # Can be somewhat glitchy. For best results, set NUM_RAYS to 360
NUM_WALLS = 5 # The amount of randomly generated walls
PIXEL_PER_MM = 10
#------------------

screen = pygame.display.set_mode(WINDOW_SIZE)
display = pygame.Surface(WINDOW_SIZE)

mx, my = pygame.mouse.get_pos()
lastClosestPoint = (0, 0)
running = True
rays = []
walls = []
particles = []
beams = []

class Ray:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.dir = (math.cos(angle), math.sin(angle))

    def update(self, mx, my):
        self.x = mx
        self.y = my

    def checkCollision(self, wall):
        x1 = wall.start_pos[0]
        y1 = wall.start_pos[1]
        x2 = wall.end_pos[0]
        y2 = wall.end_pos[1]

        x3 = self.x
        y3 = self.y
        x4 = self.x + self.dir[0]
        y4 = self.y + self.dir[1]
    
        # Using line-line intersection formula to get intersection point of ray and wall
        # Where (x1, y1), (x2, y2) are the ray pos and (x3, y3), (x4, y4) are the wall pos
        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        numerator = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
        if denominator == 0:
            return None
        
        t = numerator / denominator
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator

        if 1 > t > 0 and u > 0:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            collidePos = [x, y]
            return collidePos

class Beam:
    def __init__(self,x,y,z,direction='south',visible=True,color='green',width=1) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.direction = direction
        self.color = color
        self.width = width
        self.points = []
        self.visible=visible

    def update(self, mx, my, mz,direction='south',visible=True):
        self.x = mx
        self.y = my
        self.z = mz
        self.direction = direction
        self.visible = visible

    def draw(self):
        V_LED = 4.0
        I_LED = 5.0

        c_lambda = 0.398

        def beam_angle(half_angle):
            return 4*np.pi*(np.sin(half_angle/2)**2)

        def beer_lambert(z):
            return np.exp(-1*c_lambda*z)

        def E_LED(theta,z):
            # return (V_LED*I_LED*beer_lambert(z)*np.power(np.cos(theta),3))/z**2
            return (V_LED*I_LED*beer_lambert(z)*(np.cos(theta)**2))/z**2
        
        def polarToCartesian(r,theta):
            offset = 0
            if(self.direction == 'south'):
                offset = np.pi/2
            elif(self.direction == 'east'):
                offset = 0
            elif(self.direction == 'north'):
                offset = -np.pi/2
            elif(self.direction == 'west'):
                offset = -np.pi
            theta += offset
            x = r*np.cos(theta)
            y = r*np.sin(theta)
            return (x,y)

        # 60 deg half angle 
        # thetas = np.arange(-np.pi/2, np.pi/2,0.01)
        thetas = np.arange(-np.pi/3, np.pi/3,0.001)
        z = self.z
        self.points = [(self.x,self.y)]
        pointColorIntensities = [1.0]
        # centerIntensity = E_LED(0,z)
        centerIrradiance = E_LED(0,z)
        # print("center irradiance: ", centerIntensity)
        for theta in thetas:    
            # rayIntensity = E_LED(theta,z)
            pointIrradiance = E_LED(theta,z)
            percentIrradiance = pointIrradiance/centerIrradiance
            pointColorIntensities.append(percentIrradiance)
            # r = (rayIntensity/centerIntensity)*z
            # print("equi irradiance: ", E_LED(theta,r))
            # x, y = polarToCartesian(r,theta)
            x, y = polarToCartesian((z/np.cos(theta)),theta)
            x *= PIXEL_PER_MM
            y *= PIXEL_PER_MM
            x += self.x
            y += self.y
            self.points.append((x,y))
        
        for i,point in enumerate(self.points):
            opacity = 255*pointColorIntensities[i]
            elem = pygame.draw.aaline(display,(0,255,0,10),(self.x,self.y),point)
        # if self.visible:
            # pygame.draw.aalines(display,self.color,self.points)
            # beam equipotential bounary
            # pygame.draw.polygon(display,(0,255,0),self.points,self.width)
            
class Wall:
    def __init__(self, start_pos, end_pos, color = 'white'):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.slope_x = end_pos[0] - start_pos[0]
        self.slope_y = end_pos[1] - start_pos[1]
        if self.slope_x == 0:
            self.slope = 0
        else:
            self.slope = self.slope_y / self.slope_x
        self.length = math.sqrt(self.slope_x**2 + self.slope_y**2)

    def draw(self):
        pygame.draw.line(display, self.color, self.start_pos, self.end_pos, 3)

for i in range(0, 360, int(360/NUM_RAYS)):
    rays.append(Ray(mx, my, math.radians(i)))

def drawRays(rays, walls, color = 'white'):
    global lastClosestPoint
    for ray in rays:
        closest = 100000
        closestPoint = None
        for wall in walls:
            intersectPoint = ray.checkCollision(wall)
            if intersectPoint is not None:
                # Get distance between ray source and intersect point
                ray_dx = ray.x - intersectPoint[0]
                ray_dy = ray.y - intersectPoint[1]
                # If the intersect point is closer than the previous closest intersect point, it becomes the closest intersect point
                distance = math.sqrt(ray_dx**2 + ray_dy**2)
                if (distance < closest):
                    closest = distance
                    closestPoint = intersectPoint

        if closestPoint is not None:
            pygame.draw.line(display, color, (ray.x, ray.y), closestPoint)
            if SOLID_RAYS:
                pygame.draw.polygon(display, color, [(mx, my), closestPoint, lastClosestPoint])
                lastClosestPoint = closestPoint

def generateWalls():
    walls.clear()

    walls.append(Wall((0, 0), (WINDOW_SIZE[0], 0)))
    walls.append(Wall((0, 0), (0, WINDOW_SIZE[1])))
    walls.append(Wall((WINDOW_SIZE[0], 0), (WINDOW_SIZE[0], WINDOW_SIZE[1])))
    walls.append(Wall((0, WINDOW_SIZE[1]), (WINDOW_SIZE[0], WINDOW_SIZE[1])))

    for i in range(NUM_WALLS):
        start_x = random.randint(0, WINDOW_SIZE[0])
        start_y = random.randint(0, WINDOW_SIZE[1])
        end_x = random.randint(0, WINDOW_SIZE[0])
        end_y = random.randint(0, WINDOW_SIZE[1])
        walls.append(Wall((start_x, start_y), (end_x, end_y)))

def generateBeams():
    beamParams = []
    # the first beam will follow the mouse
    beams.append(Beam(WINDOW_SIZE[0]/2,0,50))


def draw():
    display.fill((3, 252, 252))

    # for wall in walls:
    #     wall.draw()

    for particle in particles:
        particle.draw()

    # drawRays([ray for ray in rays], [wall for wall in walls])

    for beam in beams:
        beam.draw()

    screen.blit(display, (0, 0))

    pygame.display.update()

generateBeams()
# generateWalls()
z_wheel = 10
temp_direction = ''
while running:
    mx, my = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()
            pygame.quit()

        if event.type == KEYDOWN:
            # Re-randomize walls on Space
            if event.key == pygame.K_SPACE:
               generateWalls()
            if event.key == K_UP:
                temp_direction = 'north'
            if event.key == K_LEFT:
                temp_direction = 'west'
            if event.key == K_RIGHT:
                temp_direction = 'east'
            if event.key == K_DOWN:
                temp_direction = 'south'
        
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 4:
                if z_wheel < WINDOW_SIZE[0]:
                    z_wheel += 1
            elif event.button == 5:
                if z_wheel > 1:
                    z_wheel -= 1
            else:
                beams.append(Beam(mx,my,z_wheel,temp_direction,True))        

    for ray in rays:
        ray.update(mx, my)

    beams[0].update(mx,my,z_wheel,temp_direction,pygame.mouse.get_focused())

    draw()



