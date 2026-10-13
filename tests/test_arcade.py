import unittest
import pygame
from football.app import App
from football.director import direct

class ArcadeTests(unittest.TestCase):
 def test_match_camera_replay_and_dashboard(self):
  app=App(); app.three_d=False
  try:
   self.assertTrue(app.match_view)
   app.draw(.016)
   app.switch_camera(); app.draw(.016)
   direct(app.match,'Storm scores a long shot')
   app.capture_goals()
   for time in (0,.5,1.5,2.9,3.5):
    app.replay_time=time; app.draw(.016)
   self.assertEqual(app.match.score,[0,1])
   app.switch_view(); app.draw(.016)
   self.assertFalse(app.match_view)
   self.assertGreater(len(app.buttons),30)
  finally:
   app.executor.shutdown(); pygame.quit()
