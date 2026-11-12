"""Regression checks for Chad's 0.2.7 import and its documented audit findings."""
import copy
import json
from pathlib import Path
import unittest
from decimal import Decimal

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]


class RevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = json.loads((ROOT / 'build/mrv-pod.schema.json').read_text())
        cls.supplied = json.loads((ROOT / 'tests/fixtures/chad-2026-11-05/mrv-pod.schema.json').read_text())
        cls.example = yaml.safe_load((ROOT / 'examples/Project-with-monitoring.yaml').read_text())

    def validator(self, schema):
        return jsonschema.validators.validator_for(schema)(
            schema, format_checker=jsonschema.FormatChecker())

    def test_supplied_schema_differs_only_in_root_closure(self):
        self.assertIs(self.supplied['additionalProperties'], True)
        self.assertIs(self.generated['additionalProperties'], False)
        supplied = copy.deepcopy(self.supplied)
        supplied['additionalProperties'] = False
        self.assertEqual(supplied, self.generated)

    def test_schema_metaschema_and_example(self):
        for schema in (self.supplied, self.generated):
            jsonschema.validators.validator_for(schema).check_schema(schema)
            self.validator(schema).validate(self.example)

    def test_root_unknown_property_is_rejected(self):
        example = copy.deepcopy(self.example)
        example['unknown_property'] = 'typo'
        self.assertTrue(list(self.validator(self.generated).iter_errors(example)))
        self.validator(self.supplied).validate(example)

    def test_identifiers_are_required(self):
        for name in ('Project', 'ReportingPeriod', 'MonitoringPlan', 'StaticValue', 'Measurement', 'Result'):
            definition = self.generated if name == 'Project' else self.generated['$defs'][name]
            self.assertIn('id', definition['required'], name)

    def test_example_references_and_acyclic_results(self):
        p = self.example
        periods = {x['id'] for x in p['reporting_periods']}
        self.assertEqual(len(periods), len(p['reporting_periods']))
        self.assertIn(p['reporting']['current_period'], periods)
        self.assertIn(p['reporting']['initial_period'], periods)
        m = p['monitoring']
        pools = {kind: {x['id']: x for x in m[key]} for kind, key in (
            ('plan', 'monitoring_plans'), ('static', 'static_values'),
            ('measurement', 'measurements'), ('result', 'results'))}
        for kind, key in (('plan', 'monitoring_plans'), ('static', 'static_values'),
                          ('measurement', 'measurements'), ('result', 'results')):
            self.assertEqual(len(pools[kind]), len(m[key]), kind)
        for measurement in m['measurements']:
            self.assertIn(measurement['plan'], pools['plan'])
        for result in m['results']:
            self.assertIn(result['period'], periods)
            for item in result.get('inputs', []):
                self.assertIn(item['ref'], pools[item['kind']])
        def visit(key, ancestors):
            self.assertNotIn(key, ancestors, 'Cyclic result inputs')
            for item in pools['result'][key].get('inputs', []):
                if item['kind'] == 'result':
                    visit(item['ref'], ancestors | {key})
        for key in pools['result']:
            visit(key, set())

    def test_worked_example_arithmetic_to_declared_precision(self):
        m = self.example['monitoring']
        s = {x['id']: Decimal(str(x['value']['value'])) for x in m['static_values']}
        values = [Decimal(str(x['value']['value'])) for x in m['measurements']]
        mean = sum(values) / len(values)
        baseline = s['static-baseline-fuel'] * s['static-ef'] * s['static-fnrb']
        project = mean * s['static-ef'] * s['static-fnrb']
        expected = {'result-project-fuel-mean': mean, 'result-baseline-emissions': baseline,
                    'result-project-emissions': project, 'result-net-reduction': baseline - project}
        for result in m['results']:
            self.assertLessEqual(abs(Decimal(str(result['output']['value'])) - expected[result['id']]),
                                 Decimal('0.00005'))


if __name__ == '__main__':
    unittest.main()
