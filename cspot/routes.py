
def includeme(config):
    config.add_route('home', '/')

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

    # Item Records

    config.add_route('project:records', '/projects/{project_id}/records',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:record:add', '/projects/{project_id}/records/add',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:record', '/projects/{project_id}/records/{record_id}',
                     factory='cspot.views.projects.project_factory')

    # Forms

    config.add_route('project:item_form', '/project/{project_id}/forms/item_form',
                     factory='cspot.views.projects.project_factory')

    config.add_route('project:feedback_form', '/project/{project_id}/forms/feedback_form',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:base', '/project/{project_id}/forms/{form_id}/widgets',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:add', '/project/{project_id}/forms/{form_id}/widgets/add',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget', '/project/{project_id}/forms/{form_id}/widgets/{widget_id}',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:options', '/project/{project_id}/forms/{form_id}/widgets/{widget_id}/options',
                     factory='cspot.views.projects.project_factory')

    config.add_route('form:widget:delete', '/project/{project_id}/forms/{form_id}/widgets/{widget_id}/delete',
                     factory='cspot.views.projects.project_factory')
    
