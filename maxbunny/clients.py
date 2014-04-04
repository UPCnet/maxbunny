from maxclient.wsgi import MaxClient


class MaxClientsWrapper(object):
    """
        Mimics a dict of maxclients, which tries to reload new-defined maxservers
        from disk config file if asked for a non-existant client
    """
    def __init__(self, instances):
        self.instances = instances
        self.maxclients = {}
        self.load_instances()

    def load_instances(self):
        """
            Loads instances and parses all maxservers. For each maxserver
            a maxclient with key "max_xxxxxx" is stored on self.maxclients
        """
        max_instances = [maxserver for maxserver in self.instances.sections() if maxserver.startswith('max_')]

        # Instantiate a maxclient for each maxserver
        for maxserver in max_instances:
            maxclient = MaxClient(url=self.instances.get(maxserver, 'server'), oauth_server=self.instances.get(maxserver, 'oauth_server'))
            maxclient.setActor(self.instances.get(maxserver, 'restricted_user'))
            maxclient.setToken(self.instances.get(maxserver, 'restricted_user_token'))
            self.maxclients[maxserver] = maxclient

    def __getitem__(self, key):
        """
            Retrieves a specific maxserver client. Returns None if not found
        """
        maxclient = self.maxclients.get(key, None)

        # If no maxclient found
        if maxclient is None:
            # reload maxservers from file and try it again
            self.load_instances()
            maxclient = self.maxclients.get(key, None)

        return maxclient
