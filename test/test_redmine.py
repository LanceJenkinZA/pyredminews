'''
Perform various unit tests.
'''
from unittest import TestCase
from mock import Mock
from StringIO import StringIO
import json

from redmine import Redmine


HTTP_MOCK_DATA = {}

# Sample project, retreived from two different URLs
HTTP_MOCK_DATA['/projects/1.json'] = \
    json.dumps({
        'id': 1,
        'name': 'Test 1',
        'identifier': 'test_1',
    })
HTTP_MOCK_DATA['/projects/test_1.json'] = HTTP_MOCK_DATA['/projects/1.json']

# Sample issue
HTTP_MOCK_DATA['/issues/1.json'] = \
    json.dumps({
        'id': 1,
        'subject': 'Problem with foo',
        'description': 'Foo failed to blow up as expected.',
        'project': 1,
    })

# All issues in project 1
HTTP_MOCK_DATA['/projects/1/issues.json'] = \
    json.dumps({
        'issues': [
            {
                'id': 1,
                'subject': 'Updated',
                'description': 'Foo failed to blow up.  Updated.',
                'project': 1,
            },
        ]
    })

# Closed issues in project 1
HTTP_MOCK_DATA['/projects/1/issues.json?status_id=closed'] = \
    json.dumps({
        'issues': [
            {
                'id': 2,
                'subject': 'Closed Issue',
                'description': 'This is a closed issue',
                'project': 1,
            },
        ]
    })

# Closed bugs in project 1
HTTP_MOCK_DATA['/projects/1/issues.json?status_id=closed&tracker_id=1'] = \
    json.dumps({
        'issues': [
            {
                'id': 2,
                'subject': 'Closed Issue',
                'description': 'This is a closed issue',
                'project': 1,
            },
        ]
    })
# Sample Users
HTTP_MOCK_DATA['/users.json'] = \
    json.dumps({
        'users': [
            {
                'id': 1,
                'login': 'test',
                'firstname': 'test',
                'lastname': 'test',
                'mail': 'test@testmail.com',
                'created_on': '2013-09-12T08:37:38Z',
                'last_login_on': '2014-01-16T02:42:08Z',
            },
        ]
    })

# Sample Trackers
HTTP_MOCK_DATA['/enumerations/time_entry_activities.json'] = \
    json.dumps({
        'time_entry_activities': [
            {
                'id': 1,
                'name': 'Design',
            },
        ]
    })

# Parameter order not gauranteed, just cover both
HTTP_MOCK_DATA['/projects/1/issues.json?tracker_id=1&status_id=closed'] = \
    HTTP_MOCK_DATA['/projects/1/issues.json?status_id=closed&tracker_id=1']


def mock_open_raw(page,
                  parms=None,
                  payload=None,
                  HTTPrequest=None,
                  payload_type='application/json'):
    '''
    Pretends to be the URL open method on the Redmine WS class.
    '''
    if parms is not None:
        seperator = '?'
        for key, value in parms.items():
            if key in ('limit', 'offset'):
                continue
            # Add as if it were a parameterized option
            page = '{}{}{}={}'.format(page, seperator, key, value)
            seperator = '&'

    return StringIO(HTTP_MOCK_DATA[page])


class TestProjectsAndIssues(TestCase):
    @classmethod
    def setUp(self):
        '''
        Runs once at the beginning of the test suite.
        '''
        self.test_redmine = Redmine("http://no-route.none")
        self.test_redmine.open_raw = Mock(side_effect=mock_open_raw)

    def test_get_users(self):
        '''
        Test that requests users returns users
        '''
        users = self.test_redmine.users

        for user in users:
            assert user.firstname == 'test'

    def test_get_project(self):
        '''
        Test getting a project in various ways.
        '''
        project1 = self.test_redmine.projects[1]
        projecttest = self.test_redmine.projects['test_1']
        assert id(project1) == id(projecttest)
        assert project1.name == 'Test 1'
        assert project1.id is 1
        assert project1.identifier == 'test_1'

    def test_set_project(self):
        '''
        Test updating a project.
        '''
        project1 = self.test_redmine.projects[1]
        project1.name = 'Test Foo'
        project1.save()
        # assert self.test_redmine.open_raw.assert_called_with(1)

    def test_get_issue(self):
        '''
        Test getting an issue in various ways.
        '''
        issue1 = self.test_redmine.issues[1]
        project1 = self.test_redmine.projects[1]
        assert id(issue1) == id(project1.issues[1])

        looped = False
        for issue in project1.issues:
            assert id(issue) == id(issue1)
            looped = True
        assert looped, 'Failed to iterate over the given project issues.'

        # Verify that the update data from project1 reference came in
        assert issue1.subject == 'Updated'

    def test_get_closed_issues(self):
        '''
        Test getting closed issues, and other custom queries
        '''
        project1 = self.test_redmine.projects[1]

        looped = False
        for issue in project1.issues(status_id='closed'):
            assert issue.id is 2
            looped = True
        assert looped, 'Failed to iterate over closed issues.'

        looped = False
        for issue in project1.issues(status_id='closed', tracker_id=1):
            assert issue.id is 2
            looped = True
        assert looped, 'Failed to iterate over closed bugs.'


class TestVersionBehavior(TestCase):
    '''
    Test results of instatiating various versions.
    '''
    def test_version_none(self):
        '''
        Check to ensure expected settings for Redmine with unknown version
        '''
        redm = Redmine('null')
        assert redm.version is None
        # TODO: assert redm.key_in_header is False
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert redm.time_entry_activities is not None
        assert redm.has_project_memberships is True
        assert redm.has_wiki_pages is True

    def test_version_1_0(self):
        '''
        Check to ensure expected settings for Redmine version 1.0.
        '''
        redm = Redmine('null', version=1.0)
        assert redm.version is 1.0
        # TODO: assert redm.key_in_header is False
        assert redm.issues is not None
        assert redm.projects is not None
        assert not hasattr(redm, 'users')
        assert not hasattr(redm, 'news')
        assert not hasattr(redm, 'time_entries')
        assert not hasattr(redm, 'time_entry_activities')
        assert redm.has_project_memberships is False
        assert redm.has_wiki_pages is False

    def test_version_1_1(self):
        '''
        Check to ensure expected settings for Redmine version 1.1.
        '''
        redm = Redmine('null', version=1.1)
        assert redm.version is 1.1
        assert redm.key_in_header is True
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert not hasattr(redm, 'time_entry_activities')
        assert redm.has_project_memberships is False
        assert redm.has_wiki_pages is False

    def test_version_1_2(self):
        '''
        Check to ensure expected settings for Redmine version 1.2.
        '''
        redm = Redmine('null', version=1.2)
        assert redm.version is 1.2
        assert redm.key_in_header is True
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert not hasattr(redm, 'time_entry_activities')
        assert redm.has_project_memberships is False
        assert redm.has_wiki_pages is False

    def test_version_1_3(self):
        '''
        Check to ensure expected settings for Redmine version 1.3.
        '''
        redm = Redmine('null', version=1.3)
        assert redm.version is 1.3
        assert redm.key_in_header is True
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert not hasattr(redm, 'time_entry_activities')
        assert redm.has_project_memberships is False
        assert redm.has_wiki_pages is False

    def test_version_1_4(self):
        '''
        Check to ensure expected settings for Remdine version 1.4.
        '''
        redm = Redmine('null', version=1.4)
        assert redm.version is 1.4
        assert redm.key_in_header is True
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert not hasattr(redm, 'time_entry_activities')
        assert redm.has_project_memberships is True
        assert redm.has_wiki_pages is False

    def test_version_2_1(self):
        '''
        Check to ensure expected settings for Remdine version 2.1.
        '''
        redm = Redmine('null', version=2.1)
        assert redm.version is 2.1
        assert redm.key_in_header is True
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert not hasattr(redm, 'time_entry_activities')
        assert redm.has_project_memberships is True
        assert redm.has_wiki_pages is False

    def test_version_2_2(self):
        '''
        Check to ensure expected settings for Remdine version 2.2.
        '''
        redm = Redmine('null', version=2.2)
        assert redm.version is 2.2
        assert redm.key_in_header is True
        assert redm.issues is not None
        assert redm.projects is not None
        assert redm.users is not None
        assert redm.news is not None
        assert redm.time_entry_activities is not None
        assert redm.has_project_memberships is True
        assert redm.has_wiki_pages is True
