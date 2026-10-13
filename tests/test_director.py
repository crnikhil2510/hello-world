import json
import os
import unittest
from concurrent.futures import Future
from unittest.mock import patch
from football.engine import Match
from football.director import direct, goal_path
from football.ai import plan_scene

class DirectorTests(unittest.TestCase):
 def test_directed_goal_and_invalid_command(self):
  m=Match()
  self.assertIn('Include',direct(m,'Someone scores'))
  self.assertEqual(m.score,[0,0])
  direct(m,'Akira scores a header')
  self.assertEqual(m.score,[1,0])
  self.assertEqual(m.stats[0]['shots'],1)
  self.assertEqual(m.events[-1]['method'],'header')
  self.assertEqual(goal_path(1,9,'header')[-1][0],0)
 def test_ai_validation(self):
  class Response:
   def __enter__(self): return self
   def __exit__(self,*args): pass
   def read(self): return json.dumps({'message':{'content':json.dumps({'player':'Akira','action':'Goal','method':'header','commentary':'Akira rises above the defense.'})}}).encode()
  with patch.dict(os.environ,{'FOOTBALL_AI_PROVIDER':'ollama'}),patch('urllib.request.urlopen',return_value=Response()):
   self.assertEqual(plan_scene('Akira scores',['Akira'])['action'],'Goal')
   with self.assertRaises(ValueError): plan_scene('Akira scores',['Storm'])
 def test_ai_apply_and_replay(self):
  from football.app import App
  import pygame
  a=App(); a.chat_history=[('Akira scores','pending')]
  future=Future(); future.set_result(dict(player='Akira',action='Goal',method='header',commentary='Akira rises and heads into the corner!'))
  a.ai_future=future; a.advance(.016)
  self.assertEqual(a.match.score,[1,0])
  self.assertEqual(a.match.events[-1]['source'],'ai')
  self.assertIsNotNone(a.replay)
  a.draw(.016)
  seconds=a.match.seconds
  a.advance(2); self.assertEqual(a.match.seconds,seconds)
  a.advance(3); self.assertIsNone(a.replay)
  a.executor.shutdown(); pygame.quit()
