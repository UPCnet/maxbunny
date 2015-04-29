# -*- coding: utf-8 -*-
from maxclient.wsgi import MaxClient
from maxbunny import BUNNY_NO_DOMAIN

import ConfigParser


class MaxClientsWrapper(object):
    """
        Mimics a dict of maxclients, which tries to reload new-defined maxservers
        from disk config file if asked for a non-existant client
    """
    def __init__(self, instances_config_file, default_domain, client_class=MaxClient, debug=False):
        self.default_domain = default_domain
        self.instances = instances_config_file
        self.debug = debug
        self.MaxClient = client_class

        self.load_instances()

    def get_all(self):
        for instance_id, client in self.maxclients.items():
            yield instance_id, client

    def client_ids_by_hashtag(self):
        mapping = {}
        for instance_id, client in self.maxclients.items():
            mapping[client.metadata['hashtag']] = instance_id
        return mapping

    def load_instances(self):
        """
            Loads instances and parses all maxservers. For each maxserver
            a maxclient with key == maxserver is stored on self.maxclients
        """
        self.maxclients = {}
        instances = ConfigParser.ConfigParser()
        instances.read(self.instances)

        max_instances = [maxserver for maxserver in instances.sections()]
        failed = []

        # Instantiate a maxclient for each maxserver
        # Catch exceptions related to the connection with the maxserver
        for maxserver in max_instances:
            maxclient = self.MaxClient(url=instances.get(maxserver, 'server'), debug=self.debug)
            try:
                maxclient.setActor(instances.get(maxserver, 'restricted_user'))
                maxclient.setToken(instances.get(maxserver, 'restricted_user_token'))
            except Exception as exc:
                failed.append((maxserver, exc.message))
            else:
                maxclient.metadata = {
                    "hashtag": instances.get(maxserver, 'hashtag', ''),
                    "language": instances.get(maxserver, 'language', 'ca')
                }
                self.maxclients[maxserver] = maxclient

        return failed

    def __getitem__(self, key):
        """
            Retrieves a specific maxserver client. Returns None if not found
        """
        client_domain_key = self.default_domain if key is BUNNY_NO_DOMAIN else key
        maxclient = self.maxclients.get(client_domain_key, None)
        # If no maxclient found
        if maxclient is None:
            # reload maxservers from file and try it again
            self.load_instances()
            maxclient = self.maxclients.get(client_domain_key, None)
            if maxclient is None:
                return None

        return maxclient
