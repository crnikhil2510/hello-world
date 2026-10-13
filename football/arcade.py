"""Original pixel-art broadcast renderer; no external artwork required."""
import math
import pygame
from .engine import FORMATIONS

INK=(20,29,33)
class ArcadeView:
 def __init__(self):
  self.surface=pygame.Surface((720,450))
  self.font=pygame.font.SysFont('dejavusansmono',10,bold=True)
  self.title=pygame.font.SysFont('dejavusansmono',18,bold=True)
 def project(self,x,y):
  return (round(52+x*550+(1-y)*65),round(94+y*245-x*24))
 def label(self,text,x,y,font=None,color=(245,246,229)):
  font=font or self.font
  self.surface.blit(font.render(text,False,INK),(x+1,y+1))
  self.surface.blit(font.render(text,False,color),(x,y))
 def line(self,points,width=2):
  pygame.draw.lines(self.surface,(203,229,202),False,[self.project(*p) for p in points],width)
 def sprite(self,x,y,color,number,phase,keeper=False,selected=False,celebrate=False):
  s=self.surface
  pygame.draw.ellipse(s,(24,74,53),(x-10,y-3,22,7))
  if selected:
   pygame.draw.polygon(s,(67,240,220),[(x-6,y-42),(x+6,y-42),(x,y-36)])
  skin=(225,175,128) if number%3 else (159,108,77)
  kit=(238,224,88) if keeper else color
  stride=round(math.sin(phase)*3)
  # Chunky outlined body, hair, arms and moving boots.
  pygame.draw.rect(s,INK,(x-6,y-30,13,13))
  pygame.draw.rect(s,skin,(x-4,y-27,9,10))
  pygame.draw.rect(s,(49,37,32),(x-5,y-30,11,5))
  pygame.draw.rect(s,INK,(x+2,y-23,2,2))
  pygame.draw.rect(s,(243,205,158),(x-3,y-24,3,3))
  pygame.draw.rect(s,INK,(x-8,y-18,17,14))
  pygame.draw.rect(s,kit,(x-6,y-17,13,10))
  pygame.draw.rect(s,(32,41,55),(x-6,y-7,13,5))
  for sign in (-1,1):
   arm_y=y-25 if celebrate else y-16+sign*stride
   pygame.draw.rect(s,INK,(x+sign*9-2,arm_y,5,9))
   pygame.draw.rect(s,skin,(x+sign*9-1,arm_y+2,3,5))
   leg_x=x+sign*4
   pygame.draw.rect(s,skin,(leg_x-2,y-3,4,5+sign*stride))
   pygame.draw.rect(s,INK,(leg_x-3,y+2+sign*stride,7,3))
  pygame.draw.rect(s,(245,245,239),(x-2,y-15,3,4))
 def draw(self,app,dt):
  s=self.surface; s.fill((27,73,58)); m=app.match
  # Stadium edge and crowd rendered on a low-resolution canvas.
  for y in range(0,88,8):
   for x in range(0,720,9):
    pygame.draw.rect(s,[(50,100,80),(72,117,88),(37,86,70)][(x//9+y//8)%3],(x,y,5,4))
  for i in range(12):
   points=[self.project(i/12,0),self.project((i+1)/12,0),self.project((i+1)/12,1),self.project(i/12,1)]
   pygame.draw.polygon(s,(37,119,81) if i%2 else (32,108,76),points)
  self.line([(0,0),(1,0),(1,1),(0,1),(0,0)])
  self.line([(.5,0),(.5,1)])
  self.line([(.5+.09*math.cos(a*math.tau/48),.5+.18*math.sin(a*math.tau/48)) for a in range(49)])
  for left in (True,False):
   x=0 if left else 1; direction=1 if left else -1
   self.line([(x,.22),(x+direction*.17,.22),(x+direction*.17,.78),(x,.78)])
   self.line([(x,.37),(x+direction*.055,.37),(x+direction*.055,.63),(x,.63)])
   # Raised net, posts and crossbar.
   a=self.project(x,.39); b=self.project(x,.61)
   out=-17 if left else 17
   net=[a,b,(b[0]+out,b[1]-34),(a[0]+out,a[1]-34)]
   pygame.draw.polygon(s,(40,83,73),net)
   pygame.draw.lines(s,(238,241,221),True,net,3)
   for j in range(1,7):
    u=j/7
    p=(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)
    pygame.draw.line(s,(148,183,160),p,(p[0]+out,p[1]-34))
   for j in range(1,5):
    u=j/5
    pygame.draw.line(s,(148,183,160),(a[0]+out*u,a[1]-34*u),(b[0]+out*u,b[1]-34*u))
  actors=[]
  for side,t in enumerate(m.teams):
   for i,p in enumerate(t.players):
    bx,by=FORMATIONS[t.formation][i]; target=[bx if side==0 else 1-bx,by]
    if i:
     target[0]=max(.04,min(.96,target[0]+.045*math.sin(m.seconds/17+i)))
     target[1]=max(.04,min(.96,target[1]+.03*math.sin(m.seconds/13+i)))
    pos=app.positions[side][i]
    for k in (0,1): pos[k]+=(target[k]-pos[k])*min(1,dt*(2+p.pace/50))
    if app.replay and side==app.replay.get('team_side') and i==app.replay.get('scorer_index'):
     path=app.replay['goal_path']
     progress=min(1,app.replay_time/2)
     pos= [path[0][k]+(path[-2][k]-path[0][k])*progress for k in (0,1)]
    x,y=self.project(*pos)
    actors.append((y,x,side,i,p))
  for y,x,side,i,p in sorted(actors):
   active=side==m.owner and i==m.carrier
   self.sprite(x,y,tuple(m.teams[side].color),p.number,m.seconds/2+i,keeper=p.role=='GK',selected=active,celebrate=bool(app.replay and app.replay_time>3 and active))
   if active: self.label(p.name.upper(),x-20,y-53)
  if app.replay:
   path=app.replay['goal_path']; progress=min(1,app.replay_time/3)*(len(path)-1)
   segment=min(len(path)-2,int(progress)); fraction=progress-segment
   app.ball=[path[segment][k]+(path[segment+1][k]-path[segment][k])*fraction for k in (0,1)]
   if app.replay.get('method')=='header': lift=math.sin(min(1,app.replay_time/3)*math.pi)*15
   else: lift=math.sin(min(1,app.replay_time/3)*math.pi)*5
  else:
   for k in (0,1): app.ball[k]+=(m.ball[k]-app.ball[k])*min(1,dt*6)
   lift=0
  bx,by=self.project(*app.ball)
  pygame.draw.ellipse(s,(25,72,50),(bx-4,by-1,9,4))
  pygame.draw.circle(s,(245,245,229),(bx,round(by-5-lift)),4)
  pygame.draw.rect(s,INK,(bx-1,round(by-6-lift),3,3))
  if app.camera_zoom:
   # Crop the world around the ball before drawing the fixed broadcast HUD.
   crop=pygame.Rect(max(0,min(300,bx-210)),max(0,min(90,by-131)),420,263)
   world=s.subsurface(crop).copy()
   s.blit(pygame.transform.scale(world,(720,450)),(0,0))
  # Overlay scoreboard.
  pygame.draw.rect(s,(35,39,46),(174,10,372,53),border_radius=8)
  pygame.draw.rect(s,(128,43,53),(276,28,168,30),border_radius=5)
  self.label(f'{int(m.seconds//60):02}:{int(m.seconds%60):02}',327,12)
  self.label(m.teams[0].name[:15],183,36)
  self.label(m.teams[1].name[:15],451,36)
  self.label(f'{m.score[0]} - {m.score[1]}',322,30,self.title)
  pygame.draw.rect(s,tuple(m.teams[0].color),(179,16,15,12))
  pygame.draw.rect(s,tuple(m.teams[1].color),(526,16,15,12))
  status='AI PLANNING' if app.ai_future else 'GOAL REPLAY' if app.replay else 'FULL TIME' if m.finished else 'PAUSED' if app.paused or app.chat_active else f'LIVE / {app.speed}x'
  self.label(status,15,13)
  if app.replay:
   self.label(app.replay['player']+' / '+app.replay.get('method','finish'),240, 70)
   if app.replay_time>=3: self.label('GOAL!',325,190,self.title,(255,224,94))
  # Minimap and active player cards.
  mini=pygame.Rect(285,354,150,69)
  pygame.draw.rect(s,(22,61,51),mini)
  pygame.draw.rect(s,(156,186,151),mini,1)
  pygame.draw.line(s,(156,186,151),mini.midtop,mini.midbottom)
  pygame.draw.circle(s,(156,186,151),mini.center,12,1)
  for side,t in enumerate(m.teams):
   for pos in app.positions[side]:
    pygame.draw.circle(s,tuple(t.color),(mini.x+int(pos[0]*mini.width),mini.y+int(pos[1]*mini.height)),2)
  pygame.draw.circle(s,(255,255,255),(mini.x+int(app.ball[0]*mini.width),mini.y+int(app.ball[1]*mini.height)),2)
  for side,x in ((0,28),(1,460)):
   t=m.teams[side]; p=t.players[m.carrier if side==m.owner else 0]
   self.label(f'{p.number}. {p.name.upper()} / {p.role}',x,377,self.title)
   pygame.draw.rect(s,(24,38,41),(x,404,205,8))
   pygame.draw.rect(s,(65,218,189),(x,404,int(205*p.stamina/100),8))
  self.label(m.events[-1]['commentary'][:98],15,436)
  app.canvas.blit(pygame.transform.scale(s,(1440,900)),(0,0))
