import argparse
from concurrent.futures import ThreadPoolExecutor
import math
from pathlib import Path
import pygame
from .engine import Match, FORMATIONS, TACTICS
from .director import direct
from .ai import plan_scene
from .arcade import ArcadeView

BG=(13,16,28); PANEL=(32,36,53); TEXT=(229,233,245); MUTED=(142,152,177); ACCENT=(191,103,238)
class App:
 def __init__(self,seed=7):
  pygame.init()
  self.screen=pygame.display.set_mode((1440,900),pygame.RESIZABLE)
  pygame.display.set_caption('Touchline • Football Story Simulator')
  self.canvas=pygame.Surface((1440,900)); self.clock=pygame.time.Clock()
  self.font=pygame.font.SysFont('dejavusans',14); self.small=pygame.font.SysFont('dejavusans',11); self.large=pygame.font.SysFont('dejavusans',26,bold=True)
  self.match=Match(seed); self.paused=False; self.speed=12; self.buttons=[]; self.selected=[None,None]; self.notice='Select a player, then a substitute. Five changes per team.'
  self.positions=[[list(x) for x in FORMATIONS[t.formation]] for t in self.match.teams]
  self.ball=[.5,.5]; self.scroll=0
  self.match_view=True; self.camera_zoom=False; self.arcade=ArcadeView()
  self.chat_text=""; self.chat_active=False; self.chat_history=[]
  self.replay=None; self.replay_time=0.; self.seen_goals=set(); self.executor=ThreadPoolExecutor(max_workers=1); self.ai_future=None
 def text(self,text,x,y,color=TEXT,font=None):
  self.canvas.blit((font or self.font).render(str(text),True,color),(x,y))
 def panel(self,r,title):
  pygame.draw.rect(self.canvas,PANEL,r,border_radius=12)
  self.text(title,r[0]+14,r[1]+12,ACCENT)
 def button(self,label,r,action):
  pygame.draw.rect(self.canvas,(48,54,76),r,border_radius=5)
  self.text(label,r[0]+8,r[1]+5)
  self.buttons.append((pygame.Rect(r),action))
 def cycle(self,side,field,choices):
  t=self.match.teams[side]; setattr(t,field,choices[(choices.index(getattr(t,field))+1)%len(choices)])
  self.match.event('Tactics',side,f'{t.name} switch to {t.formation}, {t.tactic.lower()} football.')
 def sub(self,side,j):
  i=self.selected[side]
  if i is not None:
   ok=self.match.substitute(side,i,j); self.notice='Substitution confirmed.' if ok else 'Change unavailable: check keeper roles or five-substitution limit.'
   self.selected[side]=None
 def team_panel(self,side,x):
  t=self.match.teams[side]
  self.panel((x,88,285,735),t.name)
  self.button(t.formation,(x+12,125,105,29),lambda:self.cycle(side,'formation',list(FORMATIONS)))
  self.button(t.tactic,(x+126,125,147,29),lambda:self.cycle(side,'tactic',TACTICS))
  self.text('XI   •   click to replace',x+12,166,MUTED)
  for i,p in enumerate(t.players):
   y=190+i*33
   r=pygame.Rect(x+8,y,269,31)
   if self.selected[side]==i: pygame.draw.rect(self.canvas,(74,63,99),r,border_radius=4)
   self.text(f'{p.number:02}  {p.name}',x+15,y+3,t.color)
   self.text(p.role,x+150,y+4,MUTED,self.small)
   self.text(f'{p.stamina:.0f}%',x+220,y+3)
   pygame.draw.rect(self.canvas,(60,65,80),(x+14,y+25,245,3))
   pygame.draw.rect(self.canvas,(75,192,145),(x+14,y+25,int(245*p.stamina/100),3))
   self.buttons.append((r,lambda i=i:self.selected.__setitem__(side,i)))
  self.text(f'BENCH  •  {t.subs}/5 substitutions',x+12,566,ACCENT)
  for j,p in enumerate(t.bench):
   self.button(f'{p.number:02} {p.name}  {p.role}',(x+12,594+j*28,261,25),lambda j=j:self.sub(side,j))
  i=self.selected[side]
  if i is not None:
   p=t.players[i]
   self.text(f'PAS {p.passing}  SHOT {p.shooting}',x+12,793,MUTED,self.small)
   self.text(f'DEF {p.defending}  PACE {p.pace}',x+145,793,MUTED,self.small)
 def submit_scene(self):
  prompt=self.chat_text.strip()
  if not prompt or self.ai_future: return
  if self.match.finished: self.notice='Start a new match before directing a scene.'; return
  roster=[p.name for t in self.match.teams for p in t.players]
  self.ai_future=self.executor.submit(plan_scene,prompt,roster)
  self.chat_history.append((prompt,'AI is planning the next scene…'))
  self.notice='AI is planning…'; self.chat_text=""
 def poll_ai(self):
  if not self.ai_future or not self.ai_future.done(): return
  try:
   scene=self.ai_future.result()
   verbs={'Goal':'scores','Save':'shoots and the keeper saves','Miss':'misses','Pass':'passes'}
   command=scene['player']+' '+verbs[scene['action']]+' '+scene['method']
   response=direct(self.match,command)
   if response.startswith('Scene applied'):
    self.match.events[-1]['commentary']=scene['commentary'][:180]
    self.match.events[-1]['source']='ai'
    self.match.events[-1]['prompt']=self.chat_history[-1][0]
    response=scene['commentary'][:180]
   self.notice=response; self.capture_goals()
  except Exception as error:
   self.notice=str(error) if isinstance(error,ValueError) else 'AI response could not be applied. Try again.'
  self.chat_history[-1]=(self.chat_history[-1][0],self.notice)
  self.ai_future=None
 def capture_goals(self):
  for i,e in enumerate(self.match.events):
   if e['kind']=='Goal' and i not in self.seen_goals:
    self.seen_goals.add(i)
    self.replay=e; self.replay_time=0.
 def advance(self,dt):
  self.poll_ai()
  if self.ai_future: return
  if self.replay:
   if not self.paused:
    self.replay_time+=dt
    if self.replay_time>=4: self.replay=None
  elif not self.paused and not self.chat_active:
   self.match.step(dt*self.speed); self.capture_goals()
 def pitch(self,dt):
  r=pygame.Rect(330,372,780,405)
  pygame.draw.rect(self.canvas,(19,98,65),r,border_radius=10)
  p=pygame.Rect(350,389,740,369)
  for i in range(10):
   pygame.draw.rect(self.canvas,(20+3*(i%2),104+6*(i%2),70+3*(i%2)),(p.x+i*74,p.y,74,p.height))
  white=(178,218,198)
  pygame.draw.rect(self.canvas,white,p,2); pygame.draw.line(self.canvas,white,p.midtop,p.midbottom,2)
  pygame.draw.circle(self.canvas,white,p.center,49,2)
  for left in (True,False):
   xx=p.x if left else p.right-111
   pygame.draw.rect(self.canvas,white,(xx,p.centery-100,111,200),2)
   pygame.draw.rect(self.canvas,white,(p.x if left else p.right-35,p.centery-52,35,104),2)
   pygame.draw.rect(self.canvas,white,(p.x-8 if left else p.right,p.centery-30,8,60),2)
  for side,t in enumerate(self.match.teams):
   for i,player in enumerate(t.players):
    bx,by=FORMATIONS[t.formation][i]
    target=[bx if side==0 else 1-bx,by]
    if i>0:
     target[0]=max(.07,min(.93,target[0]+(.035 if side==self.match.owner else -.02)*math.sin(self.match.seconds/17+i)))
     target[1]=max(.06,min(.94,by+.035*math.sin(self.match.seconds/13+i)))
    pos=self.positions[side][i]
    for k in (0,1): pos[k]+=(target[k]-pos[k])*min(1,dt*(2+player.pace/50))
    xx=p.x+int(pos[0]*p.width); yy=p.y+int(pos[1]*p.height)
    pygame.draw.circle(self.canvas,(7,35,27),(xx+2,yy+3),11)
    pygame.draw.circle(self.canvas,t.color,(xx,yy),10)
    self.text(player.number,xx-5,yy-7,(26,31,41),self.small)
  for k in (0,1): self.ball[k]+=(self.match.ball[k]-self.ball[k])*min(1,dt*6)
  if self.replay:
   path=self.replay['goal_path']
   progress=min(1,self.replay_time/3)* (len(path)-1)
   segment=min(len(path)-2,int(progress)); fraction=min(1,progress-segment)
   self.ball=[path[segment][k]+(path[segment+1][k]-path[segment][k])*fraction for k in (0,1)]
   points=[(p.x+int(x*p.width),p.y+int(y*p.height)) for x,y in path]
   pygame.draw.lines(self.canvas,(246,218,113),False,points,2)
   self.text('GOAL REPLAY • '+self.replay['player']+' • '+self.replay.get('method','finish'),p.x+12,p.y+12,(255,240,166))
   if self.replay_time>=3: self.text('GOAL!',p.centerx-45,p.centery-20,ACCENT,self.large)
  center=(p.x+int(self.ball[0]*p.width),p.y+int(self.ball[1]*p.height))
  pygame.draw.circle(self.canvas,(250,250,250),center,6); pygame.draw.circle(self.canvas,(30,30,30),center,2)
 def switch_view(self): self.match_view=not self.match_view
 def switch_camera(self): self.camera_zoom=not self.camera_zoom
 def draw_match(self,dt):
  self.buttons=[]
  self.arcade.draw(self,dt)
  controls=[('Dashboard [V]',self.switch_view),('Resume' if self.paused else 'Pause',self.toggle),('Fast '+str(self.speed)+'x',self.change_speed),('Save [S]',self.save),('Load [L]',self.load),('Export [E]',self.export)]
  for i,(label,action) in enumerate(controls): self.button(label,(330+i*130,135,122,29),action)
  self.button('Wide [Z]' if self.camera_zoom else 'Close-up [Z]',(1240,60,170,30),self.switch_camera)
  self.button('Write scene',(1240,20,170,30),lambda:setattr(self,'chat_active',not self.chat_active))
  if self.chat_active or self.ai_future:
   self.panel((870,610,550,110),'AI STORY DIRECTOR')
   pygame.draw.rect(self.canvas,(45,49,68),(883,645,423,30))
   self.text((self.chat_text or 'Write what happens next…')[-52:],890,651)
   self.button('Send',(1315,645,90,30),self.submit_scene)
   self.text(self.notice[:70],884,687,MUTED,self.small)
  size=self.screen.get_size()
  self.screen.blit(pygame.transform.scale(self.canvas,size),(0,0)); pygame.display.flip()
 def draw(self,dt):
  if self.match_view:
   self.draw_match(dt); return
  self.canvas.fill(BG); self.buttons=[]
  m=self.match
  self.text('TOUCHLINE',22,20,ACCENT,self.large)
  self.button('Match view [V]',(22,50,175,30),self.switch_view)
  self.text(f'{m.teams[0].name}    {m.score[0]} : {m.score[1]}    {m.teams[1].name}',375,20,TEXT,self.large)
  self.text(f'{int(m.seconds//60):02}:{int(m.seconds%60):02}  '+('FULL TIME' if m.finished else 'PAUSED' if self.paused else 'LIVE'),650,58,ACCENT)
  self.team_panel(0,20); self.team_panel(1,1135)
  self.panel((320,88,365,265),'MATCH STATISTICS')
  labels=[('shots','Shots'),('on_target','On target'),('xg','Expected goals'),('corners','Corners'),('possession','Possession')]
  for i,(key,label) in enumerate(labels):
   vals=[s[key] for s in m.stats]
   if key=='possession': vals=[100*v/max(1,sum(vals)) for v in vals]
   y=131+i*42; self.text(label,437,y,MUTED,self.small)
   self.text(f'{vals[0]:.2f}' if key=='xg' else f'{vals[0]:.0f}',337,y+17)
   self.text(f'{vals[1]:.2f}' if key=='xg' else f'{vals[1]:.0f}',635,y+17)
   width=int(230*vals[0]/max(1,sum(vals)))
   pygame.draw.rect(self.canvas,m.teams[1].color,(391,y+20,230,6))
   pygame.draw.rect(self.canvas,m.teams[0].color,(391,y+20,width,6))
  self.panel((700,88,410,138),'MATCH EVENTS  •  scroll to browse')
  keyevents=[e for e in m.events if e['kind']!='Pass']
  end=max(0,len(keyevents)-self.scroll)
  for i,e in enumerate(keyevents[max(0,end-3):end]):
   self.text(f"{e['minute']:02}′ {e['kind']} • {e.get('player',e['team'])}",715,132+i*29,ACCENT if e['kind']=='Goal' else TEXT,self.small)
  self.panel((700,235,410,118),'STORY DIRECTOR • AI chat')
  self.text('Try: Akira beats two defenders and scores a header.',715,265,MUTED,self.small)
  pygame.draw.rect(self.canvas,(65,55,88) if self.chat_active else (43,48,67),(715,287,292,30),border_radius=4)
  self.text((self.chat_text or 'Click here to write the next scene')[-36:],722,293)
  self.buttons.append((pygame.Rect(715,287,292,30),lambda:setattr(self,'chat_active',True)))
  self.button('Send',(1014,287,80,30),self.submit_scene)
  self.text(self.chat_history[-1][1][:56] if self.chat_history else 'Enter sends • Esc leaves typing • clock waits while typing',715,326,MUTED,self.small)
  self.pitch(dt)
  self.text(self.notice,330,792,MUTED,self.small)
  controls=[('Resume' if self.paused else 'Pause',self.toggle),('Fast '+str(self.speed)+'x',self.change_speed),('Save [S]',self.save),('Load [L]',self.load),('Export [E]',self.export),('New match [N]',self.new)]
  for i,(label,action) in enumerate(controls): self.button(label,(330+i*130,827,122,32),action)
  self.text(m.events[-1]['commentary'][:145],24,875,TEXT)
  size=self.screen.get_size(); self.screen.blit(pygame.transform.smoothscale(self.canvas,size),(0,0)); pygame.display.flip()
 def toggle(self): self.paused=not self.paused
 def change_speed(self):
  speeds=[1,6,12,30,60,120]; self.speed=speeds[(speeds.index(self.speed)+1)%len(speeds)]
 def save(self): self.match.save('exports/match.json'); self.notice='Saved exports/match.json'
 def load(self):
  if self.ai_future: self.notice='Wait for the AI scene before loading.'; return
  try:
   self.match=Match.load('exports/match.json'); self.replay=None; self.seen_goals={i for i,e in enumerate(self.match.events) if e['kind']=='Goal'}; self.scroll=0; self.selected=[None,None]; self.notice='Match restored.'
  except (OSError,ValueError,KeyError,TypeError) as e: self.notice=f'Cannot load: {e}'
 def export(self): self.match.export(); self.notice='Exported exports/events.json and exports/storyboard.md'
 def new(self):
  if self.ai_future: self.notice='Wait for the AI scene before resetting.'; return
  self.match=Match(); self.replay=None; self.seen_goals=set(); self.scroll=0; self.selected=[None,None]; self.notice='New match started.'
 def run(self,frames=0,screenshot=None):
  running=True; count=0
  while running:
   dt=min(.1,self.clock.tick(60)/1000)
   for e in pygame.event.get():
    if e.type==pygame.QUIT: running=False
    elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
     w,h=self.screen.get_size(); pos=(e.pos[0]*1440/w,e.pos[1]*900/h)
     for rect,action in self.buttons:
      if rect.collidepoint(pos): action(); break
    elif e.type==pygame.MOUSEWHEEL: self.scroll=max(0,min(len(self.match.events),self.scroll+e.y))
    elif e.type==pygame.KEYDOWN:
     if self.chat_active:
      if e.key==pygame.K_RETURN: self.submit_scene()
      elif e.key==pygame.K_ESCAPE: self.chat_active=False
      elif e.key==pygame.K_BACKSPACE: self.chat_text=self.chat_text[:-1]
      elif e.unicode and len(self.chat_text)<200: self.chat_text+=e.unicode
      continue
     actions={pygame.K_SPACE:self.toggle,pygame.K_s:self.save,pygame.K_l:self.load,pygame.K_e:self.export,pygame.K_n:self.new,pygame.K_TAB:self.change_speed,pygame.K_v:self.switch_view,pygame.K_z:self.switch_camera}
     if e.key in actions: actions[e.key]()
   self.advance(dt)
   self.draw(dt); count+=1
   if frames and count>=frames: running=False
  if screenshot:
   Path(screenshot).parent.mkdir(parents=True,exist_ok=True)
   pygame.image.save(self.canvas,screenshot)
  self.executor.shutdown(wait=False,cancel_futures=True)
  pygame.quit()

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--seed',type=int,default=7); parser.add_argument('--frames',type=int,default=0)
 parser.add_argument('--screenshot'); parser.add_argument('--simulate',action='store_true')
 args=parser.parse_args()
 if args.simulate:
  m=Match(args.seed); m.step(5400); m.export(); m.save('exports/match.json')
  print(f'Full time {m.score}; {len(m.events)} events exported')
 else: App(args.seed).run(args.frames,args.screenshot)
if __name__=='__main__': main()
