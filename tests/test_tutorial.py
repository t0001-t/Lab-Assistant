import unittest
from types import SimpleNamespace
from unittest.mock import patch

import canvas_renderer as cr
from demo_project import build_demo, has_project_work, translate_demo
from locales import STRINGS
from models import Project, default_project
from tutorial_component import accept_demo_event, tutorial_config


class State(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)

class DemoTests(unittest.TestCase):
    def test_demo_content_and_roundtrip(self):
        demo, _ = build_demo('de')
        panel = demo.panels[0]
        self.assertEqual(len(panel.lanes),10)
        self.assertEqual({m.mw for m in panel.markers},{10,25,35,40,55,70,100,130,170})
        self.assertEqual(len(panel.conditions),2)
        self.assertTrue(all(len(c.values)==10 for c in panel.conditions))
        self.assertEqual(panel.arrows[0].side,'right')
        self.assertTrue(panel.groups)
        self.assertEqual(demo.export.dpi,300)
        saved=Project.from_json(demo.to_json())
        self.assertEqual(saved.panels[0].source_image.tobytes(),panel.source_image.tobytes())
        self.assertEqual(saved.panels[0].lanes[2].label_bottom,'10^{6}')

    def test_demo_exports_and_original_unchanged(self):
        demo,_=build_demo()
        panel=demo.panels[0]
        before=panel.source_image.tobytes()
        gel=panel.processed_image()
        figure=cr.render_figure(panel,gel,cr.RenderOptions(supersample=1))
        self.assertTrue(cr.png_bytes(figure).startswith(b'\x89PNG'))
        self.assertTrue(cr.pdf_bytes(figure).startswith(b'%PDF'))
        self.assertIn(cr.tiff_bytes(figure)[:2],(b'II',b'MM'))
        self.assertEqual(before,panel.source_image.tobytes())

    def test_translation_preserves_user_edits_and_geometry(self):
        demo,track=build_demo('de');p=demo.panels[0]
        p.lanes[3].label_top='Mein eigener Text'
        p.lanes[3].x_pos_rel=.37
        p.conditions[1].name='Eigene Bedingung'
        p.conditions[0].values[1]='Custom'
        p.groups[1].text='Eigene Gruppe'
        translate_demo(demo,track,'en')
        self.assertEqual(p.lanes[1].label_top,'Control')
        self.assertEqual(p.lanes[3].label_top,'Mein eigener Text')
        self.assertEqual(p.lanes[3].x_pos_rel,.37)
        self.assertEqual(p.conditions[1].name,'Eigene Bedingung')
        self.assertEqual(p.conditions[0].values[1],'Custom')
        self.assertEqual(p.groups[1].text,'Eigene Gruppe')
        translate_demo(demo,track,'de')
        self.assertEqual(p.lanes[1].label_top,'Kontrolle')
        self.assertEqual(p.lanes[3].label_top,'Mein eigener Text')

    def test_saved_project_does_not_inherit_demo_provenance(self):
        demo,track=build_demo('de')
        loaded=Project.from_json(demo.to_json())
        before=loaded.to_json()
        translate_demo(loaded,track,'en')
        self.assertEqual(before,loaded.to_json())

    def test_work_detection(self):
        p=default_project()
        self.assertFalse(has_project_work(p))
        p.lang='en'
        self.assertFalse(has_project_work(p))
        p.panels[0].lanes[0].label_top='Edited'
        self.assertTrue(has_project_work(p))
        demo,_=build_demo()
        self.assertTrue(has_project_work(demo))

    def test_only_confirmed_unique_demo_events_replace_project(self):
        project=default_project()
        state=State(project=project,ui_version=0,crop_version=0)
        calls=[]
        for event in (None,{},{'action': 'help'},{'action': 'load_demo','nonce': 'a','confirmed': False}):
            self.assertFalse(accept_demo_event(state,event,lambda:calls.append(1)))
            self.assertIs(state.project,project)
        event={'action': 'load_demo','nonce': 'a','confirmed': True,'tour': True}
        self.assertTrue(accept_demo_event(state,event,lambda:calls.append(1)))
        replacement=state.project
        self.assertFalse(accept_demo_event(state,event,lambda:calls.append(1)))
        self.assertIs(state.project,replacement)
        self.assertEqual(calls,[1])
        self.assertTrue(state.demo_start_tour)

    def test_failed_demo_build_preserves_existing_project(self):
        project=default_project();state=State(project=project,ui_version=0,crop_version=0)
        with (patch('tutorial_component.build_demo', side_effect=OSError('Missing image')),
              self.assertRaises(OSError)):
            accept_demo_event(state, {'action': 'load_demo', 'nonce': 'x', 'confirmed': True},
                              lambda: None)
        self.assertIs(state.project,project)
        self.assertEqual(state.ui_version,0)

    def test_translations_and_five_stations(self):
        for key,pair in STRINGS.items():
            if key.startswith(('onboard_','demo_')):
                self.assertTrue(all(pair),key)
        for lang in ('de','en'):
            config=tutorial_config(lang)
            self.assertEqual(len(config['steps']),5)
            for station in config['steps']:
                for target in station:
                    self.assertIn(target,config['targets'])
                    self.assertTrue(config['text']['onboard_target_'+target])
