#!/usr/bin/env python3

import datetime as dt
from unittest import mock

from django.utils import timezone
from pytest import mark, fixture
from rest_framework import status as http_status
from pytz import utc

from api.base.settings.defaults import API_BASE
from api.providers.workflows import Workflows
from framework.exceptions import HTTPError
from osf.migrations import update_provider_auth_groups
from osf.models import RegistrationSchema, DraftRegistration
from osf.utils import permissions
from osf_tests.factories import (
    AuthUserFactory,
    DraftRegistrationFactory,
    EmbargoFactory,
    NodeFactory,
    RegistrationFactory,
    RegistrationProviderFactory,
)
from tests.base import get_default_metaschema
from tests.json_api_test_app import JSONAPITestApp
from tests.test_registrations.base import RegistrationsTestBase
from website.project.metadata.schemas import _name_to_id
from website.project.views import drafts as draft_views
from website.util import api_url_for

SCHEMA_VERSION = 2


@mark.django_db
@mark.enable_bookmark_creation
class TestRegistrationViews(RegistrationsTestBase):

    def test_node_register_page_not_registration_redirects(self):
        url = self.node.web_url_for('node_register_page')
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_302_FOUND

    @mock.patch('website.archiver.tasks.archive')
    def test_node_register_page_registration(self, mock_archive):
        draft_reg = DraftRegistrationFactory(branched_from=self.node, user=self.node.creator)
        reg = self.node.register_node(get_default_metaschema(), self.auth, draft_reg, None)
        url = reg.web_url_for('node_register_page')
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK

    def test_non_admin_can_view_node_register_page(self):
        non_admin = AuthUserFactory()
        self.node.add_contributor(
            non_admin,
            permissions.DEFAULT_CONTRIBUTOR_PERMISSIONS,
            auth=self.auth,
            save=True
        )
        reg = RegistrationFactory(project=self.node)
        url = reg.web_url_for('node_register_page')
        res = self.app.get(url, auth=non_admin.auth)
        assert res.status_code == http_status.HTTP_200_OK

    def test_is_public_node_register_page(self):
        self.node.is_public = True
        self.node.save()
        reg = RegistrationFactory(project=self.node)
        reg.is_public = True
        reg.save()
        url = reg.web_url_for('node_register_page')
        res = self.app.get(url, auth=None)
        assert res.status_code == http_status.HTTP_200_OK

    @mock.patch('framework.celery_tasks.handlers.enqueue_task', mock.Mock())
    def test_register_template_page_backwards_comptability(self):
        # Historically metaschema's were referenced by a slugified version
        # of their name.
        reg = self.draft.register(
            auth=self.auth,
            save=True
        )
        url = reg.web_url_for(
            'node_register_template_page',
            metaschema_id=_name_to_id(self.meta_schema.name),
        )
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK

    def test_register_template_page_redirects_if_not_registration(self):
        url = self.node.web_url_for(
            'node_register_template_page',
            metaschema_id=self.meta_schema._id,
        )
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_302_FOUND


@mark.enable_bookmark_creation
class TestDraftRegistrationViews(RegistrationsTestBase):

    def test_draft_before_register_page(self):
        url = self.draft_url('draft_before_register_page')
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK

    def test_get_draft_registration(self):
        url = self.draft_api_url('get_draft_registration')
        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK
        assert res.json['pk'] == self.draft._id

    def test_get_draft_registration_deleted(self):
        self.draft.deleted = timezone.now()
        self.draft.save()
        self.draft.reload()

        url = self.draft_api_url('get_draft_registration')
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_410_GONE

    def test_get_draft_registration_invalid(self):
        url = self.node.api_url_for('get_draft_registration', draft_id='13123123')
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_404_NOT_FOUND

    def test_get_draft_registration_not_admin(self):
        url = self.draft_api_url('get_draft_registration')
        res = self.app.get(url, auth=self.non_admin.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    def test_get_draft_registrations_only_gets_drafts_for_that_node(self):
        dummy = NodeFactory()

        # Drafts for dummy node
        for i in range(5):
            d = DraftRegistrationFactory(
                initiator=self.user,
                branched_from=dummy,
                meta_schema=self.meta_schema,
                schema_data={}
            )

        found = [self.draft]
        # Drafts for self.node
        for i in range(3):
            d = DraftRegistrationFactory(
                initiator=self.user,
                branched_from=self.node,
                meta_schema=self.meta_schema,
                schema_data={}
            )
            found.append(d)
        url = self.node.api_url_for('get_draft_registrations')

        res = self.app.get(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK
        # 3 new, 1 from setUp
        assert len(res.json['drafts']) == 4
        for draft in res.json['drafts']:
            assert draft['pk'] in [f._id for f in found]

    def test_new_draft_registration_POST(self):
        target = NodeFactory(creator=self.user)
        payload = {
            'schema_name': self.meta_schema.name,
            'schema_version': self.meta_schema.schema_version
        }
        url = target.web_url_for('new_draft_registration')

        res = self.app.post(url, payload, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_302_FOUND
        target.reload()
        draft = DraftRegistration.objects.get(branched_from=target)
        assert draft.registration_schema == self.meta_schema

    def test_new_draft_registration_on_registration(self):
        target = RegistrationFactory(user=self.user)
        payload = {
            'schema_name': self.meta_schema.name,
            'schema_version': self.meta_schema.schema_version
        }
        url = target.web_url_for('new_draft_registration')
        res = self.app.post(url, payload, auth=self.user.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    def test_update_draft_registration_cant_update_registered(self):
        metadata = {
            'summary': {'value': 'updated'}
        }
        assert metadata != self.draft.registration_metadata
        payload = {
            'schema_data': metadata,
            'schema_name': 'OSF-Standard Pre-Data Collection Registration',
            'schema_version': 1
        }
        self.draft.register(self.auth, save=True)
        url = self.node.api_url_for('update_draft_registration', draft_id=self.draft._id)

        res = self.app.put_json(url, payload, auth=self.user.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    def test_edit_draft_registration_page_already_registered(self):
        self.draft.register(self.auth, save=True)
        url = self.node.web_url_for('edit_draft_registration_page', draft_id=self.draft._id)
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    def test_update_draft_registration(self):
        metadata = {
            'summary': {
                'value': 'updated',
                'comments': []
            }
        }
        assert metadata != self.draft.registration_metadata
        payload = {
            'schema_data': metadata,
            'schema_name': 'Open-Ended Registration',
            'schema_version': 2
        }
        url = self.node.api_url_for('update_draft_registration', draft_id=self.draft._id)

        res = self.app.put_json(url, payload, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK

        open_ended_schema = RegistrationSchema.objects.get(name='Open-Ended Registration', schema_version=2)

        self.draft.reload()
        assert open_ended_schema == self.draft.registration_schema
        assert metadata == self.draft.registration_metadata

    def test_update_draft_registration_special_filename(self):
        # Metadata dict is copied from the PUT request to /project/<pid>/drafts/<draft_id>/
        # when adding a file as a supplemental file to a draft registration
        metadata = {
            'summary': {
                'value': None,
                'comments': [],
                'extra': []
            },
            'uploader': {
                'value': 'Cafe&LunchMenu.pdf',
                'comments': [],
                'extra': [{
                    'fileId': 'h8zsj',
                    'data': {
                        'id': 'osfstorage/5ea6ff395288ad0d931c17f5',
                        'type': 'files',
                        'links': {
                            'move': 'http://localhost:7777/v1/resources/vdbcr/providers/osfstorage/5ea6ff395288ad0d931c17f5',
                            'upload': 'http://localhost:7777/v1/resources/vdbcr/providers/osfstorage/5ea6ff395288ad0d931c17f5?kind=file',
                            'delete': 'http://localhost:7777/v1/resources/vdbcr/providers/osfstorage/5ea6ff395288ad0d931c17f5',
                            'download': 'http://localhost:7777/v1/resources/vdbcr/providers/osfstorage/5ea6ff395288ad0d931c17f5'
                        },
                        'extra': {
                            'guid': None,
                            'version': 1,
                            'downloads': 0,
                            'checkout': None,
                            'latestVersionSeen': {
                                'user': 'bd53u',
                                'seen': True
                            },
                            'hashes': {
                                'md5': '2919727d545c2a93ea89c3442d2545c5',
                                'sha256': '2161a32cfe1cbbfbd73aa541fdcb8c407523a8828bfd7a031362e1763a74e8ad'
                            }
                        },
                        'kind': 'file',
                        'name': 'Cafe&LunchMenu.pdf',
                        'path': '/5ea6ff395288ad0d931c17f5',
                        'provider': 'osfstorage',
                        'materialized': '/Cafe&LunchMenu.pdf',
                        'etag': 'c9248ce917b428c7cae6a7fd45a42b83952db882c4009f0bdf9603a43eab663b',
                        'contentType': None,
                        'modified': '2020-04-27T15:50:18.365664+00:00',
                        'modified_utc': '2020-04-27T15:50:18.365664+00:00',
                        'created_utc': '2020-04-27T15:50:18.365664+00:00',
                        'size': 805847,
                        'sizeInt': 805847,
                        'resource': 'vdbcr',
                        'permissions': {
                            'view': True,
                            'edit': True
                        },
                        'nodeId': 'vdbcr',
                        'nodeUrl': '/vdbcr/',
                        'nodeApiUrl': '/api/v1/project/vdbcr/',
                        'accept': {
                            'maxSize': 5120,
                            'acceptedFiles': True
                        },
                        'waterbutlerURL': 'http://localhost:7777'
                    },
                    'selectedFileName': 'Cafe&LunchMenu.pdf',
                    'nodeId': 'vdbcr',
                    'viewUrl': '/project/vdbcr/files/osfstorage/5ea6ff395288ad0d931c17f5',
                    'sha256': '2161a32cfe1cbbfbd73aa541fdcb8c407523a8828bfd7a031362e1763a74e8ad',
                    'descriptionValue': ''
                }]
            }
        }
        assert metadata != self.draft.registration_metadata
        payload = {
            'schema_data': metadata,
            'schema_name': 'Open-Ended Registration',
            'schema_version': 2
        }
        url = self.node.api_url_for('update_draft_registration', draft_id=self.draft._id)

        res = self.app.put_json(url, payload, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_200_OK

        open_ended_schema = RegistrationSchema.objects.get(name='Open-Ended Registration', schema_version=2)

        self.draft.reload()
        assert open_ended_schema == self.draft.registration_schema
        assert metadata['uploader']['value'] == self.draft.registration_metadata['uploader']['value']
        assert metadata['uploader']['extra'][0]['selectedFileName'] == self.draft.registration_metadata['uploader']['extra'][0]['selectedFileName']


    def test_update_draft_registration_non_admin(self):
        metadata = {
            'summary': {
                'value': 'updated',
                'comments': []
            }
        }
        assert metadata != self.draft.registration_metadata
        payload = {
            'schema_data': metadata,
            'schema_name': 'OSF-Standard Pre-Data Collection Registration',
            'schema_version': 1
        }
        url = self.node.api_url_for('update_draft_registration', draft_id=self.draft._id)

        res = self.app.put_json(url, payload, auth=self.non_admin.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

        # group admin cannot update draft registration
        res = self.app.put_json(url, payload, auth=self.group_mem.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    def test_delete_draft_registration(self):
        assert 1 == DraftRegistration.objects.filter(deleted__isnull=True).count()
        url = self.node.api_url_for('delete_draft_registration', draft_id=self.draft._id)

        res = self.app.delete(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_204_NO_CONTENT
        assert 0 == DraftRegistration.objects.filter(deleted__isnull=True).count()

    def test_delete_draft_registration_non_admin(self):
        assert 1 == DraftRegistration.objects.filter(deleted__isnull=True).count()
        url = self.node.api_url_for('delete_draft_registration', draft_id=self.draft._id)

        res = self.app.delete(url, auth=self.non_admin.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN
        assert 1 == DraftRegistration.objects.filter(deleted__isnull=True).count()

        # group admin cannot delete draft registration
        res = self.app.delete(url, auth=self.group_mem.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    @mock.patch('website.archiver.tasks.archive')
    def test_delete_draft_registration_registered(self, mock_register_draft):
        self.draft.register(auth=self.auth, save=True)
        url = self.node.api_url_for('delete_draft_registration', draft_id=self.draft._id)

        res = self.app.delete(url, auth=self.user.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN

    @mock.patch('website.archiver.tasks.archive')
    def test_delete_draft_registration_approved_and_registration_deleted(self, mock_register_draft):
        self.draft.register(auth=self.auth, save=True)
        self.draft.registered_node.is_deleted = True
        self.draft.registered_node.save()

        assert 1 == DraftRegistration.objects.filter(deleted__isnull=True).count()
        url = self.node.api_url_for('delete_draft_registration', draft_id=self.draft._id)

        res = self.app.delete(url, auth=self.user.auth)
        assert res.status_code == http_status.HTTP_204_NO_CONTENT
        assert 0 == DraftRegistration.objects.filter(deleted__isnull=True).count()

    def test_only_admin_can_delete_registration(self):
        non_admin = AuthUserFactory()
        assert 1 == DraftRegistration.objects.filter(deleted__isnull=True).count()
        url = self.node.api_url_for('delete_draft_registration', draft_id=self.draft._id)

        res = self.app.delete(url, auth=non_admin.auth, expect_errors=True)
        assert res.status_code == http_status.HTTP_403_FORBIDDEN
        assert 1 == DraftRegistration.objects.filter(deleted__isnull=True).count()

    def test_get_metaschemas(self):
        url = api_url_for('get_metaschemas')
        res = self.app.get(url).json
        assert len(res['meta_schemas']) == RegistrationSchema.objects.get_latest_versions().count()

    def test_get_metaschemas_all(self):
        url = api_url_for('get_metaschemas', include='all')
        res = self.app.get(url)
        assert res.status_code == http_status.HTTP_200_OK
        assert len(res.json['meta_schemas']) == RegistrationSchema.objects.filter(active=True).count()

    def test_validate_embargo_end_date_too_soon(self):
        registration = RegistrationFactory(project=self.node)
        today = dt.datetime.today().replace(tzinfo=utc)
        too_soon = today + dt.timedelta(days=5)
        try:
            draft_views.validate_embargo_end_date(too_soon.isoformat(), registration)
        except HTTPError as e:
            assert e.code == http_status.HTTP_400_BAD_REQUEST
        else:
            self.fail()

    def test_validate_embargo_end_date_too_late(self):
        registration = RegistrationFactory(project=self.node)
        today = dt.datetime.today().replace(tzinfo=utc)
        too_late = today + dt.timedelta(days=(4 * 365) + 1)
        try:
            draft_views.validate_embargo_end_date(too_late.isoformat(), registration)
        except HTTPError as e:
            assert e.code == http_status.HTTP_400_BAD_REQUEST
        else:
            self.fail()

    def test_validate_embargo_end_date_ok(self):
        registration = RegistrationFactory(project=self.node)
        today = dt.datetime.today().replace(tzinfo=utc)
        too_late = today + dt.timedelta(days=12)
        try:
            draft_views.validate_embargo_end_date(too_late.isoformat(), registration)
        except Exception:
            self.fail()

    def test_check_draft_state_registered(self):
        reg = RegistrationFactory()
        self.draft.registered_node = reg
        self.draft.save()
        try:
            draft_views.check_draft_state(self.draft)
        except HTTPError as e:
            assert e.code == http_status.HTTP_403_FORBIDDEN
        else:
            self.fail()

    def test_check_draft_state_registered_but_deleted(self):
        reg = RegistrationFactory()
        self.draft.registered_node = reg
        reg.is_deleted = True
        self.draft.save()
        try:
            draft_views.check_draft_state(self.draft)
        except Exception:
            self.fail()

    def test_check_draft_state_ok(self):
        try:
            draft_views.check_draft_state(self.draft)
        except Exception:
            self.fail()


@mark.django_db
class TestModeratorRegistrationViews:

    @fixture
    def app(self):
        return JSONAPITestApp()

    @fixture
    def moderator(self):
        return AuthUserFactory()

    @fixture
    def provider(self, moderator):
        provider = RegistrationProviderFactory()
        update_provider_auth_groups()
        provider.get_group('moderator').user_set.add(moderator)
        provider.reviews_workflow = Workflows.PRE_MODERATION.value
        provider.save()
        return provider

    @fixture
    def embargoed_registration(self, provider):
        embargo = EmbargoFactory()
        registration = embargo.target_registration
        registration.provider = provider
        registration.update_moderation_state()
        registration.save()
        return registration


    # API paths for registrations that are not publically available on non-public Registrations
    PROTECTED_REGISTRATION_SUB_ROUTES = [
        '',
        'bibliographic_contributors',
        'children',
        'comments',
        'implicit_contributors',
        'files',
        'citation',
        'forks',
        'identifiers',
        'institutions',
        'linked_nodes',
        'linked_registrations',
        'linked_by_nodes',
        'linked_by_registrations',
        'logs',
        'node_links',
        'relationships/institutions',
        'relationships/linked_nodes',
        'relationships/linked_registrations',
        'relationships/subjects',
        'subjects',
        'wikis',
    ]
    @fixture(params=PROTECTED_REGISTRATION_SUB_ROUTES)
    def registration_subpath(self, request, embargoed_registration):
        url = f'/{API_BASE}registrations/{embargoed_registration._id}/{request.param}'
        if request.param:
            url += '/'
        return url


    def test_moderator_cannot_view_subpath_of_initial_registration(
        self, app, embargoed_registration, moderator, registration_subpath):
        # Moderators should not have non-standard access to a registration
        # before it is submitted for moderation by its authors
        assert embargoed_registration.moderation_state == 'initial'

        resp = app.get(registration_subpath, auth=moderator.auth, expect_errors=True)
        assert resp.status_code == 403

    def test_moderator_can_view_subpath_of_submitted_registration(
        self, app, embargoed_registration, moderator, registration_subpath):
        # Moderators may need to see details of the pending registration
        # in order to determine whether to give approval
        embargoed_registration.embargo.accept()
        embargoed_registration.refresh_from_db()
        assert embargoed_registration.moderation_state == 'pending'

        resp = app.get(registration_subpath, auth=moderator.auth)
        assert resp.status_code == 200

    def test_moderator_can_viw_subpath_of_embargoed_registration(
        self, app, embargoed_registration, moderator, registration_subpath):
        # Moderators may need to see details of an embargoed registration
        # to determine if there is a need to withdraw before it becomes public
        embargoed_registration.embargo.accept()
        embargoed_registration.embargo.accept(user=moderator)
        embargoed_registration.refresh_from_db()
        assert embargoed_registration.moderation_state == 'embargo'

        resp = app.get(registration_subpath, auth=moderator.auth)
        assert resp.status_code == 200
