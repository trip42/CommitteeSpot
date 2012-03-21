
def includeme(config):

    # General

    config.add_route('home', '/')
    config.add_route('terms', '/terms')
    config.add_route('privacy', '/privacy')

    # Authentication

    config.add_route('auth:login', '/login')
    config.add_route('auth:logout', '/logout')
    config.add_route('auth:signup', '/signup')

    # User Profile

    config.add_route('user:myprofile', '/profile',
                     factory='cspot.views.users.user_factory')

    config.add_route('user:profile', '/profile/{user_id}',
                     factory='cspot.views.users.user_factory')

    # Projects

    config.add_route('project:list', '/projects')
    config.add_route('project:add', '/projects/add')
    config.add_route('project', '/projects/{project_id}',
                     factory='cspot.views.projects.project_factory')
    config.add_route('project:settings', '/projects/{project_id}/settings',
                     factory='cspot.views.projects.project_factory')

    # Item Records

    config.add_route('project:records', '/projects/{project_id}/records',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:record:add', '/projects/{project_id}/records/add',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:record', '/projects/{project_id}/records/{record_id}',
                     factory='cspot.views.projects.project_factory')
    
    config.add_route('project:record:download', '/project/{project_id}/records/{record_id}/widgets/{widget_id}/download/{filename}',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:item_form', '/project/{project_id}/forms/item_form',
                     factory='cspot.views.projects.project_factory')

    # Feedback Form Creation

    config.add_route('project:feedback_form', '/project/{project_id}/forms/feedback_form',
                     factory='cspot.views.projects.project_factory')

    # Team

    config.add_route('project:team', '/project/{project_id}/team',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:team:add', '/project/{project_id}/team/add',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:team:remove', '/project/{project_id}/team/{user_id}/remove',
                     factory='cspot.views.projects.project_factory')

    # Distribution

    config.add_route('project:distribute', '/project/{project_id}/distribute',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:distribute:history', '/project/{project_id}/distribute/history',
                     factory='cspot.views.projects.project_factory')

    # Submit Feedback

    config.add_route('project:feedback', '/project/{project_id}/feedback',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:feedback:view', '/project/{project_id}/feedback/view',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:feedback:download', '/project/{project_id}/feedback/download',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:feedback:item', '/project/{project_id}/feedback/{item_id}',
                     factory='cspot.views.projects.project_factory')

    # Forms

    config.add_route('form:widget:base', '/project/{project_id}/forms/{form_id}/widgets',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:add', '/project/{project_id}/forms/{form_id}/widgets/add',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:sort_order', '/project/{project_id}/forms/{form_id}/widgets/sort_order',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget', '/project/{project_id}/forms/{form_id}/widgets/{widget_id}',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:options', '/project/{project_id}/forms/{form_id}/widgets/{widget_id}/options',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:delete', '/project/{project_id}/forms/{form_id}/widgets/{widget_id}/delete',
                     factory='cspot.views.projects.project_factory')

    
