from mock import patch
import unittest
import json

from tests.factories.model.project import ProjectFactory
from tests.factories.model.application import ApplicationFactory
from tds.views import cli


class TestApplicationOutputFormatter(unittest.TestCase):

    def setUp(self):
        self.apps = [ApplicationFactory(),
                     ApplicationFactory()]

    def test_single_app_blocks_format(self):
        output = cli.format_application(self.apps[0])
        expected = cli.APPLICATION_TEMPLATE.format(self=self.apps[0])
        self.assertEqual(output, expected)

    def test_mult_app_blocks_format(self):
        output = cli.format_application(self.apps)
        expected = "\n\n{block}\n\n{block}".format(
            block=cli.APPLICATION_TEMPLATE.format(self=self.apps[0]),
        )
        self.assertEqual(output, expected)

    @patch('tagopsdb.PackageDefinition.to_dict')
    def test_single_app_json_format(self, to_dict):
        to_dict.return_value = vars(self.apps[0])
        output = json.loads(cli.format_application(self.apps[0], "json"))
        expected = vars(self.apps[0])
        self.assertEqual(output, expected)

    @patch('tagopsdb.PackageDefinition.to_dict')
    def test_mult_app_json_format(self, to_dict):
        to_dict.return_value = vars(self.apps[0])
        output = json.loads(cli.format_application(self.apps, "json"))
        expected = [vars(self.apps[0]), vars(self.apps[0])]
        self.assertEqual(output, expected)

    def test_single_app_table_format(self):
        output = cli.format_application(self.apps[0], "table")
        expected = "| Application   |\n|---------------|\n| fake_package  |"
        self.assertEqual(output, expected)


# class TestProjectOutputFormatter(unittest.TestCase):
#
#     def setUp(self):
#         self.projects = [ProjectFactory(name="proj1"),
#                          ProjectFactory(name="proj2")]
#
#     def test_single_proj_blocks_format(self):
#         output = cli.format_project(self.projects[0])
#         assert False, output
