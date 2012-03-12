
def includeme(config):
    config.add_route('home', '/')

    # Authentication

    config.add_route('auth:login', '/login')
    config.add_route('auth:logout', '/logout')
    config.add_route('auth:signup', '/signup')

    # User Profile

    config.add_route('user:profile', '/profile')

    # Projects

    config.add_route('project:list', '/projects')
    config.add_route('project:add', '/projects/add')
    config.add_route('project:records', '/projects/{project_id}/records')
    config.add_route('project:record:add', '/projects/{project_id}/records/add')
    config.add_route('project:record', '/projects/{project_id}/records/{record_id}')
    


