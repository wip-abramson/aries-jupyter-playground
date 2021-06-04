import asyncio

class Connection:

    def __init__(self, connection_id, auth_policy = None):
        self.connection_id = connection_id
        self.auth_policy = auth_policy
        self.is_active = asyncio.Future()
        self.is_trusted = asyncio.Future()
        self.verified_attributes = []
        self.self_attested_attributes = []

