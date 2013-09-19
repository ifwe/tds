###
### NOTE: This is just here as a placeholder for how tests should
###       be written; none of the tests here will actually run
###       and should be replaced
###

import json

import mock
import unittest2 as unittest

import tds.project
import tds.utils
import tds.rest.views

from tagopsdb.exceptions import RepoException


mock_valid_find = {'name': 'spambuild',
                   'id': 1,
                   'project_type': 'application',
                   'pkg_type': 'jenkins',
                   'pkg_name': 'spambuild',
                   'app_name': 'spambuild',
                   'path': 'spambuild',
                   'arch': 'noarch',
                   'build_host': 'dfakebuild01.tag-dev.com',
                   'environment': False,
                   'app_types': ['spambuild']}

mock_invalid_find = {'name': 'hambuild'}


class ProjectControllerTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('tds.project.Project', spec_set=True,
                **{'find.return_value': mock_valid_find})
    @mock.patch('tds.main.TDS', autospec=True,
                **{'check_user_auth.return_value': True,
                   'initialize_db.return_value': True})
    def test_valid_project(self, *args):
        name = tds.project.Project.find.return_value['name']
        response = tds.rest.views.get_project(name)
        self.assertEqual(response.status_code, 200)

        obj = json.loads(response.data)
        self.assertEqual(obj['name'], name)

        project_keys = sorted(['app_name', 'app_types', 'arch', 'build_host',
                               'environment', 'id', 'name', 'path',
                               'pkg_name', 'pkg_type', 'project_type'])
        self.assertListEqual(sorted(obj.keys()), project_keys)

    @mock.patch('tds.project.Project', spec_set=True,
                **{'find.side_effect': RepoException})
    @mock.patch('tds.main.TDS', autospec=True,
                **{'check_user_auth.return_value': True,
                   'initialize_db.return_value': True})
    def test_invalid_project(self, *args):
        name = mock_valid_find['name'] + 'invalid'
        response = tds.rest.views.get_project(name)
        self.assertEqual(response.status_code, 404)

        obj = json.loads(response.data)
        self.assertEqual(obj['error'], 'No such project')


class ProjectModelTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('tds.project.repo',
                **{'find_app_location.return_value':
                       type('fake', (object,), mock_valid_find)})
    def test_find_valid(self, *args):
        name = 'spambuild'
        project = tds.project.Project.find(name)

        self.assertEqual(project.name, name)
        self.assertIn('id', project.__dict__.keys())

    @mock.patch('tds.project.repo',
                **{'find_app_location.side_effect': RepoException})
    def test_find_invalid(self, repo):
        name = mock_invalid_find.get('name')
        self.assertRaises(RepoException, tds.project.Project.find, name)
