"""Offline checks for validation and baseline comparison; no database access."""
import copy
import csv
from pathlib import Path
import tempfile
import unittest

from evals.check_reference import FIELDS, compare_results, read_questions


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.rows = read_questions(Path(__file__).with_name('golden_questions.csv'))

    def invalid_csv(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'questions.csv'
            with path.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValueError):
                read_questions(path)

    def test_duplicate_ids_rejected(self):
        self.rows[1]['id'] = self.rows[0]['id']
        self.invalid_csv(self.rows)

    def test_decline_sql_rejected(self):
        self.rows[6]['reference_sql'] = 'SELECT 1'
        self.invalid_csv(self.rows)

    def test_multiple_statements_rejected(self):
        self.rows[0]['reference_sql'] = 'SELECT 1; COMMIT; SELECT 2'
        self.invalid_csv(self.rows)

    def test_insufficient_provenance_rejected(self):
        for row in self.rows:
            row['source'] = 'other'
        self.invalid_csv(self.rows)

    def test_changed_answers_and_scheduled_evidence(self):
        baseline = {'question_set_sha256': 'same', 'passed': True,
                    'successful_scheduled_run_ids': ['first'],
                    'results': [{'id': 'Q01', 'status': 'pass', 'columns': ['value'], 'rows': [[1]]},
                                {'id': 'Q02', 'status': 'decline_not_executed'}]}
        current = copy.deepcopy(baseline)
        current['results'][0]['rows'] = [[2]]
        current['successful_scheduled_run_ids'] += ['second', 'third']
        result = compare_results(current, baseline)
        self.assertEqual(result['changed'], ['Q01'])
        self.assertTrue(result['at_least_two_more_scheduled_syncs'])
        current['successful_scheduled_run_ids'] = ['first']
        self.assertFalse(compare_results(current, baseline)['at_least_two_more_scheduled_syncs'])

    def test_question_changes_invalidate_comparison(self):
        with self.assertRaises(ValueError):
            compare_results({'question_set_sha256': 'new'}, {'question_set_sha256': 'old'})


if __name__ == '__main__':
    unittest.main()
