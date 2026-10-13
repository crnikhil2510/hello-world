"""Seeded, resumable football simulation."""
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path

FORMATIONS = {
 '4-3-3': [(0.06,.5),(.24,.12),(.24,.37),(.24,.63),(.24,.88),(.48,.23),(.43,.5),(.48,.77),(.77,.15),(.82,.5),(.77,.85)],
 '4-4-2': [(0.06,.5),(.24,.12),(.24,.37),(.24,.63),(.24,.88),(.50,.12),(.46,.37),(.46,.63),(.50,.88),(.80,.33),(.80,.67)],
 '3-5-2': [(0.06,.5),(.25,.22),(.22,.5),(.25,.78),(.50,.08),(.48,.3),(.42,.5),(.48,.7),(.50,.92),(.80,.33),(.80,.67)]}
TACTICS = ['Balanced','Attack','Defend','Press','Possession']

@dataclass
class Player:
 name: str
 number: int
 role: str
 passing: int
 shooting: int
 defending: int
 pace: int
 stamina: float = 100.

@dataclass
class Team:
 name: str
 color: list
 players: list
 bench: list
 formation: str = '4-3-3'
 tactic: str = 'Balanced'
 subs: int = 0
 def power(self,skill):
  return sum(getattr(p,skill)*(.45+.55*p.stamina/100) for p in self.players[1:])/10

class Match:
 def __init__(self,seed=7):
  self.rng=random.Random(seed)
  self.teams=[]
  rosters=[('Northbridge FC',[232,238,250],'Vale Sato Reed Silva Lane Kaito Park Ren Cruz Akira Blake Noah Jin Leo Kai Hugo Finn Theo'),
           ('Amber Wolves',[255,196,54],'Costa Ramos Ito Stone Gray Haru Mori Cole Riku Storm Yu Ezra Luca Max Ken Alex Omar Eli')]
  for name,color,names in rosters:
   ps=[Player(n,i+1,'GK' if i in (0,11) else 'DEF' if i<5 or i in (12,13) else 'MID' if i<8 or i in (14,15) else 'FWD',*[self.rng.randint(55,92) for _ in range(4)]) for i,n in enumerate(names.split())]
   self.teams.append(Team(name,color,ps[:11],ps[11:]))
  self.seconds=0.; self.next_event=6.; self.score=[0,0]
  self.stats=[dict(shots=0,on_target=0,xg=0.,corners=0,possession=0.) for _ in range(2)]
  self.events=[]; self.owner=0; self.carrier=7; self.ball=[.5,.5]; self.finished=False
  self.event('Kickoff',0,'The rivalry begins. Both teams search for an opening.')
 def event(self,kind,side,text,**extra):
  self.events.append(dict(second=round(self.seconds,2),minute=int(self.seconds//60),kind=kind,team=self.teams[side].name,commentary=text,score=self.score.copy(),**extra))
 def step(self,dt):
  if self.finished: return
  end=min(5400.,self.seconds+dt)
  while self.seconds<end:
   span=min(end-self.seconds,max(0.,self.next_event-self.seconds))
   self.stats[self.owner]['possession']+=span
   for t in self.teams:
    for p in t.players: p.stamina=max(10,p.stamina-span*(.0058 if t.tactic=='Press' else .0045))
   self.seconds+=span
   if self.seconds>=self.next_event:
    self.play(); self.next_event+=self.rng.uniform(7,18)
  if self.seconds>=5400:
   self.finished=True
   self.event('Full time',self.owner,f'Full time: {self.score[0]}–{self.score[1]}. The final whistle seals the story.')
 def play(self):
  weights=[t.power('passing')*(1.12 if t.tactic=='Possession' else 1)*(1.08 if t.formation=='3-5-2' else 1) for t in self.teams]
  self.owner=0 if self.rng.random()<weights[0]/sum(weights) else 1
  t=self.teams[self.owner]; opp=self.teams[1-self.owner]
  self.carrier=self.rng.randrange(1,11); p=t.players[self.carrier]
  x,y=FORMATIONS[t.formation][self.carrier]; self.ball=[x if self.owner==0 else 1-x,y]
  roll=self.rng.random()
  attack=1.3 if t.tactic=='Attack' else 1.12 if t.tactic=='Press' else .85 if t.tactic=='Defend' else 1
  attack *= (1.10 if t.formation=='4-3-3' else 1) * (.85+t.power('pace')/500)
  if roll<.065*attack:
   s=self.stats[self.owner]; s['shots']+=1
   quality=min(.6,max(.04,p.shooting/100*.32*(p.stamina/100+.5)*75/opp.power('defending')))
   s['xg']+=quality; target=self.rng.random()<.30+p.shooting/200
   if target: s['on_target']+=1
   keeper=opp.players[0]
   goal=target and self.rng.random()<min(.8,quality/(.30+p.shooting/200)*(1.15-keeper.defending/250))
   if goal:
    self.score[self.owner]+=1
    from .director import goal_path
    method=self.rng.choice(['header','free kick','long shot','dribble and finish'])
    self.event('Goal',self.owner,f'{p.name} scores with a {method}! The crowd erupts.',player=p.name,xg=round(quality,3),method=method,team_side=self.owner,scorer_index=self.carrier,goal_path=goal_path(self.owner,self.carrier,method))
    self.ball=[.5,.5]
   else:
    self.event('Save' if target else 'Miss',self.owner,f'{p.name} shoots — '+(f'{keeper.name} makes the save!' if target else 'the ball flashes wide.'),player=p.name,xg=round(quality,3))
    if self.rng.random()<.3:
     s['corners']+=1; self.event('Corner',self.owner,f'{t.name} win a corner. Defenders brace for the delivery.')
  elif roll<.12:
   self.event('Tackle',1-self.owner,f'{opp.players[self.rng.randrange(1,5)].name} intercepts {p.name}. Momentum shifts.')
  else:
   self.event('Pass',self.owner,f'{p.name} links up with {t.players[self.rng.randrange(1,11)].name} to build the attack.',player=p.name)
 def substitute(self,side,index,bench_index):
  t=self.teams[side]
  if self.finished or t.subs>=5 or not 0<=index<11 or not 0<=bench_index<len(t.bench): return False
  outgoing=t.players[index]; incoming=t.bench[bench_index]
  if (outgoing.role=='GK')!=(incoming.role=='GK'): return False
  t.bench.pop(bench_index); t.players[index]=incoming; t.subs+=1
  self.event('Substitution',side,f'{incoming.name} replaces {outgoing.name}. Fresh legs enter the battle.',incoming=incoming.name,outgoing=outgoing.name)
  return True
 def save(self,path):
  data={k:v for k,v in self.__dict__.items() if k not in ('rng','teams')}
  data['teams']=[asdict(t) for t in self.teams]; data['rng']=self.rng.getstate()
  Path(path).parent.mkdir(parents=True,exist_ok=True)
  Path(path).write_text(json.dumps(data,indent=2))
 @classmethod
 def load(cls,path):
  data=json.loads(Path(path).read_text()); m=cls(); state=data.pop('rng')
  def tuples(v): return tuple(tuples(x) for x in v) if isinstance(v,list) else v
  m.rng.setstate(tuples(state)); teams=data.pop('teams')
  m.teams=[Team(**{**t,'players':[Player(**p) for p in t['players']],'bench':[Player(**p) for p in t['bench']]}) for t in teams]
  m.__dict__.update(data); return m
 def export(self,directory='exports'):
  root=Path(directory); root.mkdir(parents=True,exist_ok=True)
  (root/'events.json').write_text(json.dumps(self.events,indent=2))
  lines=['# Match storyboard',f'{self.teams[0].name} {self.score[0]} – {self.score[1]} {self.teams[1].name}']
  for e in self.events:
   if e['kind']!='Pass': lines.append(f"**{e['minute']}′ {e['kind']}** — {e['commentary']}")
  (root/'storyboard.md').write_text(chr(10).join(lines))
