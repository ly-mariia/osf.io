
from framework import request, redirect, get_current_user, update_counters, push_status_message
from ..decorators import must_not_be_registration, must_be_valid_project, \
    must_be_contributor, must_be_contributor_or_public
from framework.auth import must_have_session_auth
from framework.forms.utils import sanitize
from ..model import NodeWikiPage
from .node import _view_project

import difflib
from .. import show_diff

def project_project_wikimain(pid):
    return redirect('/project/%s/wiki/home' % str(pid))

def project_node_wikihome(pid, nid):
    return redirect('/project/{pid}/node/{nid}/wiki/home'.format(pid=pid, nid=nid))

@must_be_valid_project # returns project
@must_be_contributor_or_public # returns user, project
@update_counters('node:{pid}')
@update_counters('node:{nid}')
def project_wiki_compare(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = kwargs['user']
    wid = kwargs['wid']

    node_to_use = node or project

    pw = node_to_use.get_wiki_page(wid)

    if pw:
        compare_id = kwargs['compare_id']
        comparison_page = node_to_use.get_wiki_page(wid, compare_id)
        if comparison_page:
            current = pw.content
            comparison = comparison_page.content
            sm = difflib.SequenceMatcher(None, comparison, current)
            content = show_diff(sm)
            content = content.replace('\n', '<br />')
            versions = [NodeWikiPage.load(i) for i in reversed(node_to_use.wiki_pages_versions[wid])]
            versions_json = []
            for version in versions:
                versions_json.append({
                    'version' : version.version,
                    'user_fullname' : version.user.fullname,
                    'date' : version.date,
                })
            rv = {
                'pageName' : wid,
                'content' : content,
                'versions' : versions_json,
                'is_current' : True,
                'is_edit' : True,
                'version' : pw.version,
            }
            rv.update(_view_project(node_to_use, user))
            return rv
    push_status_message('Not a valid version')
    return redirect('{}wiki/{}'.format(
        node_to_use.url(),
        wid
    ))

@must_be_valid_project # returns project
@must_be_contributor # returns user, project
@update_counters('node:{pid}')
@update_counters('node:{nid}')
def project_wiki_version(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = kwargs['user']
    wid = kwargs['wid']
    vid = kwargs['vid']

    node_to_use = node or project

    pw = node_to_use.get_wiki_page(wid, version=vid)

    if pw:
        rv = {
            'pageName' : wid,
            'content' : pw.html,
            'version' : pw.version,
            'is_current' : pw.is_current,
            'is_edit' : False,
        }
        rv.update(_view_project(node_to_use, user))
        return rv

    push_status_message('Not a valid version')
    return redirect('{}wiki/{}'.format(
        node_to_use.url(),
        wid
    ))

@must_be_valid_project # returns project
@update_counters('node:{pid}')
@update_counters('node:{nid}')
def project_wiki_page(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    wid = kwargs['wid']

    user = get_current_user()
    node_to_use = node or project

    if not node_to_use.is_public:
        if user:
            if not node_to_use.is_contributor(user):
                push_status_message('You are not a contributor on this page')
                return redirect('/')
        else:
            push_status_message('You are not authorized to view this page')
            return redirect('/account')

    pw = node_to_use.get_wiki_page(wid)

    # todo breaks on /<script>; why?

    if pw:
        version = pw.version
        is_current = pw.is_current
        content = pw.html
    else:
        version = 'NA'
        is_current = False
        content = 'There does not seem to be any content on this page; sorry.'

    toc = [
        {
            'id' : child._primary_key,
            'title' : child.title,
            'category' : child.category,
            'pages' : child.wiki_pages_current.keys() if child.wiki_pages_current else [],
        }
        for child in node_to_use.nodes
        if not child.is_deleted
    ]

    rv = {
        'pageName' : wid,
        'page' : pw,
        'version' : version,
        'content' : content,
        'is_current' : is_current,
        'is_edit' : False,
        'pages_current' : node_to_use.wiki_pages_versions.keys(),
        'toc' : toc,
    }
    rv.update(_view_project(node_to_use, user))
    return rv

@must_have_session_auth # returns user
@must_be_valid_project # returns project
@must_be_contributor # returns user, project
@must_not_be_registration
def project_wiki_edit(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = kwargs['user']
    wid = kwargs['wid']

    node_to_use = node or project

    pw = node_to_use.get_wiki_page(wid)

    if pw:
        version = pw.version
        is_current = pw.is_current
        content = pw.content
    else:
        version = 'NA'
        is_current = False
        content = ''
    rv = {
        'pageName' : wid,
        'page' : pw,
        'version' : version,
        'content' : content,
        'is_current' : is_current,
        'is_edit' : True,
    }
    rv.update(_view_project(node_to_use, user))
    return rv

@must_have_session_auth # returns user
@must_be_valid_project # returns project
@must_be_contributor # returns user, project
@must_not_be_registration
def project_wiki_edit_post(*args, **kwargs):
    project = kwargs['project']
    node = kwargs['node']
    user = kwargs['user']
    wid = kwargs['wid']

    if node:
        node_to_use = node
        base_url = '/project/{pid}/node/{nid}/wiki'.format(pid=project._primary_key, nid=node._primary_key)
    else:
        node_to_use = project
        base_url = '/project/{pid}/wiki'.format(pid=project._primary_key)

    if wid != sanitize(wid):
        push_status_message("This is an invalid wiki page name")
        return redirect(base_url)

    node_to_use.updateNodeWikiPage(wid, request.form['content'], user)

    return redirect(base_url + '/{wid}'.format(wid=wid))
