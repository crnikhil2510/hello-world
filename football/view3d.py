"""Perspective 3D software renderer using Pygame, with original low-poly meshes."""
import math
import pygame
from .engine import FORMATIONS

class View3D:
 def __init__(self):
  self.angle=.25
  self.faces=[]
 def project(self,x,y,z=0):
  c,s=math.cos(self.angle),math.sin(self.angle)
  horizontal=x*c-y*s
  forward=x*s+y*c
  distance=85 if self.close else 135
  height=65 if self.close else 95
  elevation=math.atan2(height,distance)
  ce,se=math.cos(elevation),math.sin(elevation)
  depth=(distance-forward)*ce+(height-z)*se
  vertical=(z-height)*ce+(distance-forward)*se
  return (round(720+horizontal*1120/max(1,depth)),round(460-vertical*1120/max(1,depth)),depth)
 def world(self,x,y,z=0):
  return ((x-.5)*105,(y-.5)*68,z)
 def polygon(self,canvas,points,color):
  pygame.draw.polygon(canvas,color,[self.project(*p)[:2] for p in points])
 def line(self,canvas,points,color=(222,239,218),width=2):
  pygame.draw.lines(canvas,color,False,[self.project(*p)[:2] for p in points],width)
 def box(self,x,y,z,w,d,h,color):
  points=[(x+dx*w/2,y+dy*d/2,z+dz*h) for dx,dy,dz in
          [(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  for indices,shade in [((0,1,5,4),.7),((1,2,6,5),.85),((2,3,7,6),.8),((3,0,4,7),.6),((4,5,6,7),1.1)]:
   vertices=[self.project(*points[i]) for i in indices]
   self.faces.append((sum(v[2] for v in vertices)/4,[v[:2] for v in vertices],tuple(min(255,int(c*shade)) for c in color)))
 def draw(self,app,dt):
  self.close=app.camera_zoom
  canvas=app.canvas; m=app.match; self.faces=[]
  canvas.fill((101,156,184))
  pygame.draw.rect(canvas,(44,70,76),(0,245,1440,655))
  self.polygon(canvas,[(-65,-46,0),(65,-46,0),(65,46,0),(-65,46,0)],(43,93,66))
  # Raised stands behind the playing field.
  for y in (-43,43):
   for row in range(4):
    self.box(0,y+(row*2 if y>0 else -row*2),row*1.5,116,2,1.2,(82+row*12,101+row*8,117))
  for i in range(12):
   x=-52.5+i*105/12
   self.polygon(canvas,[(x,-34,.01),(x+105/12,-34,.01),(x+105/12,34,.01),(x,34,.01)],
                (43,135,78) if i%2 else (36,119,70))
  self.line(canvas,[(-52.5,-34,.03),(52.5,-34,.03),(52.5,34,.03),(-52.5,34,.03),(-52.5,-34,.03)])
  self.line(canvas,[(0,-34,.03),(0,34,.03)])
  self.line(canvas,[(9.15*math.cos(i*math.tau/64),9.15*math.sin(i*math.tau/64),.04) for i in range(65)])
  for sign in (-1,1):
   x=sign*52.5
   self.line(canvas,[(x,-20,.04),(x-sign*16.5,-20,.04),(x-sign*16.5,20,.04),(x,20,.04)])
   self.line(canvas,[(x,-9,.04),(x-sign*5.5,-9,.04),(x-sign*5.5,9,.04),(x,9,.04)])
   # Solid posts and crossbar.
   for y in (-3.66,3.66): self.box(x,y,0,.22,.22,2.44,(240,242,231))
   self.box(x,0,2.44,.22,7.54,.22,(240,242,231))
  labels=[]
  for side,t in enumerate(m.teams):
   for i,p in enumerate(t.players):
    bx,by=FORMATIONS[t.formation][i]; target=[bx if side==0 else 1-bx,by]
    if i:
     target[0]=max(.04,min(.96,target[0]+.045*math.sin(m.seconds/17+i)))
     target[1]=max(.04,min(.96,target[1]+.03*math.sin(m.seconds/13+i)))
    pos=app.positions[side][i]
    for k in (0,1): pos[k]+=(target[k]-pos[k])*min(1,dt*(2+p.pace/50))
    active=side==m.owner and i==m.carrier
    if app.replay and side==app.replay.get('team_side') and i==app.replay.get('scorer_index'):
     path=app.replay['goal_path']; progress=min(1,app.replay_time/2)
     pos=[path[0][k]+(path[-2][k]-path[0][k])*progress for k in (0,1)]
    x,y,_=self.world(*pos)
    skin=(224,172,123) if p.number%3 else (156,103,74)
    kit=(240,225,65) if p.role=='GK' else tuple(t.color)
    stride=math.sin(m.seconds/2+i)*.28
    self.polygon(canvas,[(x+.65*math.cos(j*math.tau/12),y+.5*math.sin(j*math.tau/12),.05) for j in range(12)],(29,91,55))
    # Boots, articulated legs, shorts, torso, arms and head.
    for sign in (-1,1):
     self.box(x+sign*.20,y+sign*stride,0,.27,.44,.16,(26,29,33))
     self.box(x+sign*.20,y+sign*stride,.16,.22,.24,.68,skin)
    self.box(x,y,.8,.70,.40,.35,(32,45,66))
    self.box(x,y,1.12,.75,.43,.80,kit)
    for sign in (-1,1):
     arm_z=1.65 if app.replay and app.replay_time>3 and active else 1.0
     self.box(x+sign*.51,y-sign*stride,arm_z,.22,.24,.65,skin)
    self.box(x,y,1.96,.46,.44,.44,skin)
    self.box(x,y,2.30,.49,.46,.13,(46,34,27))
    if active:
     px,py,_=self.project(x,y,3.4)
     pygame.draw.polygon(canvas,(64,232,216),[(px-8,py-13),(px+8,py-13),(px,py)])
     labels.append((p.name.upper(),px-25,py-35))
  if app.replay:
   path=app.replay['goal_path']; progress=min(1,app.replay_time/3)*(len(path)-1)
   segment=min(len(path)-2,int(progress)); fraction=progress-segment
   app.ball=[path[segment][k]+(path[segment+1][k]-path[segment][k])*fraction for k in (0,1)]
   lift=math.sin(min(1,app.replay_time/3)*math.pi)*(3 if app.replay.get('method')=='header' else 1.3)
  else:
   for k in (0,1): app.ball[k]+=(m.ball[k]-app.ball[k])*min(1,dt*6)
   lift=0
  x,y,_=self.world(*app.ball)
  self.box(x,y,.15+lift,.42,.42,.42,(246,245,230))
  for _,points,color in sorted(self.faces,key=lambda face:face[0],reverse=True):
   pygame.draw.polygon(canvas,color,points)
  # Netting has height and depth behind each goal.
  for sign in (-1,1):
   x=sign*52.5; back=x+sign*2
   for j in range(9):
    y=-3.66+j*7.32/8
    self.line(canvas,[(x,y,2.44),(back,y,2.44),(back,y,0)],(170,190,182),1)
   for j in range(6):
    z=j*2.44/5
    self.line(canvas,[(back,-3.66,z),(back,3.66,z)],(170,190,182),1)
  for name,x,y in labels: app.text(name,x,y,(240,246,240),app.small)
  pygame.draw.rect(canvas,(24,32,44),(335,16,770,105),border_radius=12)
  app.text(f'{m.teams[0].name}    {m.score[0]} : {m.score[1]}    {m.teams[1].name}',355,48,font=app.large)
  app.text(f'{int(m.seconds//60):02}:{int(m.seconds%60):02}  •  3D MATCH',615,89,(92,226,191))
  status='AI PLANNING' if app.ai_future else 'GOAL REPLAY' if app.replay else 'FULL TIME' if m.finished else 'PAUSED' if app.paused or app.chat_active else f'LIVE / {app.speed}x'
  app.text(status,25,25,(239,241,238),app.large)
  app.text('Arrow keys rotate camera • Z zoom • B pixel/3D',25,62)
  if app.replay:
   app.text(app.replay['player']+' • '+app.replay.get('method','finish'),520,190,(255,235,124),app.large)
   if app.replay_time>=3: app.text('GOAL!',640,260,(255,235,124),app.large)
  mini=pygame.Rect(605,746,230,110)
  pygame.draw.rect(canvas,(24,60,49),mini,border_radius=4)
  pygame.draw.rect(canvas,(171,210,176),mini,1)
  pygame.draw.line(canvas,(171,210,176),mini.midtop,mini.midbottom)
  pygame.draw.circle(canvas,(171,210,176),mini.center,20,1)
  for side,t in enumerate(m.teams):
   for pos in app.positions[side]:
    pygame.draw.circle(canvas,t.color,(mini.x+int(pos[0]*mini.width),mini.y+int(pos[1]*mini.height)),3)
  pygame.draw.circle(canvas,(255,255,255),(mini.x+int(app.ball[0]*mini.width),mini.y+int(app.ball[1]*mini.height)),3)
  pygame.draw.rect(canvas,(24,32,44),(0,865,1440,35))
  app.text(m.events[-1]['commentary'][:160],20,875)
