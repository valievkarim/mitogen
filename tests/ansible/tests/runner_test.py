from __future__ import absolute_import

import json
import os
import tempfile
import unittest

import ansible_mitogen.runner


class UmaskChangingRunner(ansible_mitogen.runner.Runner):
    def _run(self):
        os.umask(0o077)
        return {
            u'rc': 0,
            u'stdout': u'',
            u'stderr': u'',
        }

    def revert(self):
        self.umask_seen_by_revert = ansible_mitogen.runner.get_umask()
        super(UmaskChangingRunner, self).revert()


class FailingUmaskChangingRunner(UmaskChangingRunner):
    def _run(self):
        os.umask(0o077)
        raise RuntimeError('boom')


class RunnerUmaskTest(unittest.TestCase):
    def setUp(self):
        self.original_umask = ansible_mitogen.runner.get_umask()
        os.umask(0o022)
        self.temp_dir = tempfile.mkdtemp()
        super(RunnerUmaskTest, self).setUp()

    def tearDown(self):
        super(RunnerUmaskTest, self).tearDown()
        os.umask(self.original_umask)
        os.rmdir(self.temp_dir)

    def make_runner(self, klass):
        return klass(
            module='test',
            service_context=None,
            json_args=json.dumps({}),
            good_temp_dir=self.temp_dir,
        )

    def test_restores_umask_before_revert(self):
        runner = self.make_runner(UmaskChangingRunner)
        runner.run()
        self.assertEqual(0o022, runner.umask_seen_by_revert)
        self.assertEqual(0o022, ansible_mitogen.runner.get_umask())

    def test_restores_umask_after_exception(self):
        runner = self.make_runner(FailingUmaskChangingRunner)
        with self.assertRaises(RuntimeError):
            runner.run()

        self.assertEqual(0o022, runner.umask_seen_by_revert)
        self.assertEqual(0o022, ansible_mitogen.runner.get_umask())
