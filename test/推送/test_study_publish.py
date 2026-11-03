import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '推送'))
from study_plan import plans, day_page
from study_publish import due_days, pending, validate, marker, relative

class StudyPublishingTests(unittest.TestCase):
    def test_every_day_has_four_hours_and_dates_are_contiguous(self):
        schedule = plans()
        self.assertEqual(len(schedule), 32)
        self.assertEqual(schedule[0]['date'], '2026-11-03')
        self.assertEqual(schedule[-1]['date'], '2026-12-04')
        for plan in schedule:
            self.assertEqual(sum(t['minutes'] for t in plan['tasks']), 240)
            self.assertEqual(len(plan['tasks']), 4)

    def test_backlog_bounds(self):
        self.assertEqual(due_days(date(2026,11,2)), [])
        self.assertEqual(len(due_days(date(2026,11,5))), 3)
        self.assertEqual(len(due_days(date(2027,1,1))), 32)
        with self.assertRaises(ValueError):
            relative(date(2026,12,5))

    def test_placeholder_is_not_completed_material(self):
        day = date(2026,11,3)
        draft = day_page(plans()[0])
        with self.assertRaises(ValueError):
            validate(draft, day)
        with self.assertRaises(ValueError):
            validate(draft+'\n'+marker(day), day)

    def test_backlog_checks_remote_not_local_placeholder(self):
        day = date(2026,11,3)
        calls = []
        def fake_git(*args):
            calls.append(args)
            if args[0] == 'ls-tree':
                return relative(day)
            if args[0] == 'show':
                return day_page(plans()[0])
            return ''
        with patch('study_publish.git', side_effect=fake_git):
            self.assertEqual(pending(day), [day])
        self.assertEqual(calls[0], ('fetch','origin','master'))

if __name__ == '__main__':
    unittest.main()
