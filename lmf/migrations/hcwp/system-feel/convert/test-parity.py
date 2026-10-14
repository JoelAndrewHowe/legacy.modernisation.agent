#!/usr/bin/env python3
"""Isolated comparator/contract rejection checks; no approved inputs modified."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
loader = importlib.machinery.SourceFileLoader('parity_runner', str(HERE / 'verify'))
spec = importlib.util.spec_from_loader(loader.name, loader)
parity = importlib.util.module_from_spec(spec)
loader.exec_module(parity)


class Rejections(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual([], parity.compare_complete({'a': [True, 1, None]}, {'a': [True, 1, None]}))

    def test_extra_key(self):
        self.assertTrue(parity.compare_complete({'a': {}}, {'a': {'unexpected': 1}}))

    def test_missing_key(self):
        self.assertTrue(parity.compare_complete({'a': 1}, {}))

    def test_boolean_not_integer(self):
        self.assertTrue(parity.compare_complete({'a': True}, {'a': 1}))

    def test_missing_row(self):
        self.assertTrue(parity.compare_complete({'rows': [1, 2]}, {'rows': [1]}))

    def test_extra_row(self):
        self.assertTrue(parity.compare_complete({'rows': [1]}, {'rows': [1, 2]}))

    def test_reordered_rows(self):
        self.assertTrue(parity.compare_complete({'rows': [1, 2]}, {'rows': [2, 1]}))

    def test_changed_field(self):
        self.assertTrue(parity.compare_complete({'rows': [{'value': 'Recorded'}]}, {'rows': [{'value': 'Not examined'}]}))

    def test_missing_required_scenario(self):
        fixtures = json.loads((parity.PACKET / 'fixtures.json').read_text())
        contract = json.loads((parity.PACKET / 'scenarios.json').read_text())
        contract['scenarios'].pop()
        with self.assertRaises(ValueError):
            parity.reference.validate_contract(fixtures, contract)

    def test_nonrequired_scenario(self):
        fixtures = json.loads((parity.PACKET / 'fixtures.json').read_text())
        contract = json.loads((parity.PACKET / 'scenarios.json').read_text())
        contract['scenarios'][0]['required'] = False
        with self.assertRaises(ValueError):
            parity.reference.validate_contract(fixtures, contract)

    def test_converted_ordering_source(self):
        observed = parity.ordering_observation()
        self.assertEqual([{'field': 'ExaminationDate', 'direction': 'descending'}], observed['keys'])
        self.assertFalse(observed['equalDateTieBreakDefined'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Rejections))
    print(json.dumps({'executed': result.testsRun, 'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
                      'failed': len(result.failures) + len(result.errors), 'skipped': len(result.skipped)}))
    sys.exit(0 if result.wasSuccessful() and result.testsRun > 0 and not result.skipped else 1)
