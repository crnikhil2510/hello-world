import unittest
import pygame
from football.app import App
from football.director import direct

class View3DTests(unittest.TestCase):
 def test_camera_replay_and_view_switches(self):
  app=App()
  try:
   self.assertTrue(app.three_d)
   app.draw(.016)
   renderer=app.renderer3d
   near=renderer.project(5,20)[2]; far=renderer.project(5,-20)[2]
   self.assertLess(near,far)
   direct(app.match,'Akira scores a header')
   app.capture_goals()
   app.switch_camera()
   for angle in (0,.6,1.6,3.1,4.6):
    renderer.angle=angle
    for time in (0,1,2.5,3.5):
     app.replay_time=time; app.draw(.016)
     self.assertTrue(renderer.faces)
   self.assertEqual(app.match.score,[1,0])
   app.switch_dimension(); self.assertFalse(app.three_d); app.draw(.016)
   app.switch_view(); app.draw(.016); self.assertFalse(app.match_view)
  finally:
   app.executor.shutdown(); pygame.quit()
