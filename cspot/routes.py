
def includeme(config):
    config.add_route('home', '/')

    # Authentication

    config.add_route('auth:login', '/login')
    config.add_route('auth:logout', '/logout')
    config.add_route('auth:signup', '/signup')

    # User Profile

    config.add_route('user:profile', '/profile')

