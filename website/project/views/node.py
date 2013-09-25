from framework import (
    get, post, request, redirect, must_be_logged_in, push_status_message, abort,
    push_errors_to_status, app, render, Blueprint, get_user, get_current_user,
    secure_filename, jsonify, update_counters, send_file
)
from .. import (
    new_node, new_project, get_node, show_diff, get_file_tree,
)
from ..decorators import must_not_be_registration, must_be_valid_project, \
    must_be_contributor, must_be_contributor_or_public
from ..forms import NewProjectForm, NewNodeForm
from ..model import ApiKey, User, Tag, Node, NodeFile, NodeWikiPage, NodeLog
from framework.forms.utils import sanitize
from framework.auth import must_have_session_auth

from website import settings
from website import filters

from framework import analytics

import re
import json
import httplib as http

def get_node_permission(node, user):
    return {
        'is_contributor' : node.is_contributor(user),
        'can_edit' : node.is_contributor(user) and not node.is_registration,
    }

@must_have_session_auth #
@must_be_valid_project # returns project
@must_be_contributor # returns user, project
@must_not_be_registration
def edit_node(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']

    node_to_use = node or project

    form = request.form
    original_title = node_to_use.title

    if form.get('name') == 'title' and form.get('value'):
        node_to_use.title = sanitize(form['value'])

        node_to_use.add_log(
            action='edit_title',
            params={
                'project':node_to_use.node__parent[0]._primary_key if node_to_use.node__parent else None,
                'node':node_to_use._primary_key,
                'title_new':node_to_use.title,
                'title_original':original_title,
            },
            user=get_current_user(),
        )

        node_to_use.save()

    return {'status' : 'success'}

def search_user(*args, **kwargs):
    form = request.form
    query = form.get('query', '').strip()

    is_email = False
    email_re = re.search('[^@\s]+@[^@\s]+\.[^@\s]+', query)
    if email_re:
        is_email = True
        email = email_re.group(0)
        result = User.find_by_email(email)
    else:
        result = User.search(query)

    return {
        'is_email':is_email,
        'results':[
            {
                'fullname' : item.fullname,
                'gravatar' : filters.gravatar(item.username, size=settings.gravatar_size_add_contributor),
                'id' : item._primary_key,
            } for item in result
        ]
    }

##############################################################################
# New Project
##############################################################################

@must_be_logged_in
def project_new(*args, **kwargs):
    form = NewProjectForm()
    return {
        'form' : form,
    }

@must_be_logged_in
def project_new_post(*args, **kwargs):
    user = kwargs['user']
    form = NewProjectForm(request.form)
    if form.validate():
        project = new_project(form.title.data, form.description.data, user)
        return redirect('/project/' + str(project._primary_key))
    else:
        push_errors_to_status(form.errors)
    return {
        'form' : form,
    }, http.BAD_REQUEST

##############################################################################
# New Node
##############################################################################

@must_have_session_auth # returns user
@must_be_valid_project # returns project
@must_be_contributor # returns user, project
@must_not_be_registration
def project_new_node(*args, **kwargs):
    form = NewNodeForm(request.form)
    project = kwargs['project']
    user = kwargs['user']
    if form.validate():
        node = new_node(
            title=form.title.data,
            user=user,
            category=form.category.data,
            project = project,
        )
        return redirect('/project/' + str(project._primary_key))
    else:
        push_errors_to_status(form.errors)
    # todo: raise error
    return redirect('/project/' + str(project._primary_key))

@must_be_valid_project
def node_fork_page(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = get_current_user()

    if node:
        node_to_use = node
        push_status_message('At this time, only projects can be forked; however, this behavior is coming soon.')
        # todo discuss
        return redirect(node_to_use.url())
    else:
        node_to_use = project

    if node_to_use.is_registration:
        push_status_message('At this time, only projects that are not registrations can be forked; however, this behavior is coming soon.')
        # todo discuss
        return node_to_use.url()

    fork = node_to_use.fork_node(user)

    return fork.url()

@must_have_session_auth
@must_be_valid_project
@must_be_contributor_or_public # returns user, project
@update_counters('node:{pid}')
@update_counters('node:{nid}')
def node_registrations(*args, **kwargs):

    user = get_current_user()
    node_to_use = kwargs['node'] or kwargs['project']
    return _view_project(node_to_use, user)

@must_be_valid_project
@must_be_contributor_or_public # returns user, project
@update_counters('node:{pid}')
@update_counters('node:{nid}')
def node_forks(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = get_current_user()

    node_to_use = node or project
    return _view_project(node_to_use, user)

@must_be_valid_project
@must_be_contributor # returns user, project
def node_setting(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = get_current_user()

    node_to_use = node or project

    return _view_project(node_to_use, user)

##############################################################################
# View Project
##############################################################################

@must_be_valid_project
@must_not_be_registration
@must_be_contributor # returns user, project
def project_reorder_components(*args, **kwargs):
    project = kwargs['project']
    user = get_current_user()

    node_to_use = project
    old_list = [i._id for i in node_to_use.nodes if not i.is_deleted]
    new_list = json.loads(request.form['new_list'])

    if len(old_list) == len(new_list) and set(new_list) == set(old_list):
        node_to_use.nodes = new_list
        if node_to_use.save():
            return {'status' : 'success'}
    # todo log impossibility
    return {'success' : 'failure'}

##############################################################################

@must_be_valid_project
@must_be_contributor_or_public # returns user, project
def project_statistics(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = get_current_user()

    # todo not used
    node_to_use = node or project

    counters = analytics.get_day_total_list(
        'node:{}'.format(node_to_use._primary_key)
    )
    csv = '\\n'.join(['date,price'] + ['{},{}'.format(counter[0], counter[1]) for counter in counters])

    rv = {
        'csv' : csv,
    }
    rv.update(_view_project(node_to_use, user))
    return rv

###############################################################################
# Make Public
###############################################################################


@must_have_session_auth
@must_be_valid_project
@must_be_contributor
def project_set_permissions(*args, **kwargs):

    user = kwargs['user']
    permissions = kwargs['permissions']
    node_to_use = kwargs['node'] or kwargs['project']

    node_to_use.set_permissions(permissions, user)

    # todo discuss behavior
    return redirect(node_to_use.url())

@get('/project/<pid>/watch')
@must_have_session_auth # returns user or api_node
@must_be_valid_project # returns project
@must_not_be_registration
def project_watch(*args, **kwargs):
    project = kwargs['project']
    user = kwargs['user']
    project.watch(user)
    return redirect('/project/'+str(project._primary_key))

@must_have_session_auth # returns user or api_node
@must_be_valid_project # returns project
@must_be_contributor # returns user, project
@must_not_be_registration
def component_remove(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = kwargs['user']
    if node:
        node_to_use = node
    else:
        node_to_use = project

    # todo discuss behavior
    if node_to_use.remove_node(user=user):
        push_status_message('Component(s) deleted')
        return redirect('/dashboard/')
    else:
        push_status_message('Component(s) unable to be deleted')
        return redirect(node_to_use.url())



@must_be_valid_project
def view_project(*args, **kwargs):
    user = get_current_user()
    node_to_use = kwargs['node'] or kwargs['project']
    return _view_project(node_to_use, user)

def _view_project(node_to_use, user):

    return {

        'node_id' : node_to_use._primary_key,
        'node_title' : node_to_use.title,
        'node_category' : node_to_use.category,
        'node_description' : node_to_use.description,
        'node_url' : node_to_use.url(),
        'node_api_url' : node_to_use.api_url(),
        'node_is_public' : node_to_use.is_public,
        'node_date_created' : node_to_use.date_created.strftime('%Y/%m/%d %I:%M %p'),
        'node_date_modified' : node_to_use.logs[-1].date.strftime('%Y/%m/%d %I:%M %p'),

        'node_tags' : [tag._primary_key for tag in node_to_use.tags],
        'node_children' : [
            {
                'child_id' : child._primary_key,
                'child_url' : child.url(),
                'child_api_url' : child.api_url(),
            }
            for child in node_to_use.nodes
        ],

        'node_is_registration' : node_to_use.is_registration,
        'node_registered_from_url' : node_to_use.registered_from.url() if node_to_use.is_registration else '',
        'node_registered_date' : node_to_use.registered_date.strftime('%Y/%m/%d %I:%M %p') if node_to_use.is_registration else '',
        'node_registered_meta' : [
            {
                'name_no_ext' : meta.replace('.txt', ''),
                'name_clean' : clean_template_name(meta),
            }
            for meta in node_to_use.registered_meta
        ],
        'node_registrations' : [
            {
                'registration_id' : registration._primary_key,
                'registration_url' : registration.url(),
                'registration_api_url' : registration.api_url(),
            }
            for registration in node_to_use.node__registered
        ],

        'node_is_fork' : node_to_use.is_fork,
        'node_forked_from_url' : node_to_use.forked_from.url() if node_to_use.is_fork else '',
        'node_forked_date' : node_to_use.forked_date.strftime('%Y/%m/%d %I:%M %p') if node_to_use.is_fork else '',
        'node_fork_count' : len(node_to_use.fork_list),
        'node_forks' : [
            {
                'fork_id' : fork._primary_key,
                'fork_url' : fork.url(),
                'fork_api_url' : fork.api_url(),
            }
            for fork in node_to_use.node__forked
        ],

        'parent_id' : node_to_use.node__parent[0]._primary_key if node_to_use.node__parent else None,
        'parent_title' : node_to_use.node__parent[0].title if node_to_use.node__parent else None,
        'parent_url' : node_to_use.node__parent[0].url() if node_to_use.node__parent else None,

        'user_is_contributor' : node_to_use.is_contributor(user),
        'user_can_edit' : node_to_use.is_contributor(user) and not node_to_use.is_registration,

    }


@must_be_valid_project
def get_summary(*args, **kwargs):

    node_to_use = kwargs['node'] or kwargs['project']

    return {
        'summary' : {
            'pid' : node_to_use._primary_key,
            'purl' : node_to_use.url(),
            'title' : node_to_use.title,
            'registered_date' : node_to_use.registered_date.strftime('%m/%d/%y %I:%M %p') if node_to_use.registered_date else None,
            'logs' : list(reversed(node_to_use.logs._to_primary_keys()))[:3],
        }
    }

