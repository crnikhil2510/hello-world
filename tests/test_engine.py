import tempfile
import unittest
from pathlib import Path
from football.engine import Match

class MatchTests(unittest.TestCase):
 def test_full_match(self):
  m=Match(); m.step(5400)
  self.assertTrue(m.finished)
  self.assertEqual(m.seconds,5400)
  self.assertEqual(m.events[-1]['kind'],'Full time')
  self.assertAlmostEqual(sum(s['possession'] for s in m.stats),5400)
  for i,t in enumerate(m.teams):
   self.assertEqual(len(t.players),11)
   self.assertTrue(all(0<p.stamina<=100 for p in t.players))
   self.assertLessEqual(m.score[i],m.stats[i]['on_target'])
   self.assertLessEqual(m.stats[i]['on_target'],m.stats[i]['shots'])
 def test_resume_and_export(self):
  m=Match(42); m.step(1234)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'save.json'; m.save(p); restored=Match.load(p)
   m.step(4166); restored.step(4166)
   self.assertEqual(m.events,restored.events)
   self.assertEqual(m.stats,restored.stats)
   restored.export(d)
   self.assertIn('Full time',(Path(d)/'storyboard.md').read_text())
 def test_subs(self):
  m=Match(); t=m.teams[0]; original=t.players[9]
  self.assertFalse(m.substitute(0,0,1))
  self.assertEqual(len(t.bench),7)
  self.assertTrue(m.substitute(0,9,1))
  self.assertNotEqual(t.players[9],original)
  for _ in range(4): self.assertTrue(m.substitute(0,9,1))
  self.assertFalse(m.substitute(0,9,1))
 def test_pause_and_controls(self):
  from football.app import App
  import pygame
  a=App(); a.toggle(); self.assertTrue(a.paused)
  a.cycle(0,'formation',['4-3-3','4-4-2','3-5-2'])
  self.assertEqual(a.match.teams[0].formation,'4-4-2')
  a.change_speed(); self.assertEqual(a.speed,30)
  a.draw(.016); self.assertGreater(len(a.buttons),30)
  pygame.quit()
if __name__=='__main__': unittest.main()
