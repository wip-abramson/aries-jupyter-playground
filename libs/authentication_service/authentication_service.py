# stdlib
import asyncio
import logging
from typing import Dict as TypeDict
from typing import List as TypeList
from typing import Optional
from .connection import Connection
import qrcode
import time

# third party
from aries_cloudcontroller import AriesAgentController
import nest_asyncio

nest_asyncio.apply()

# logger = logging.getLogger()
# logger.setLevel(logging.INFO)


class AuthenticationService:
    def __init__(
        self,
        agent_controller: AriesAgentController,
    ) -> None:

        self.agent_controller = agent_controller

        self.agent_listeners = [
            {"topic": "connections", "handler": self._connections_handler},
            {"topic": "present_proof", "handler": self._proof_handler},
        ]

        self.agent_controller.register_listeners(self.agent_listeners, defaults=False)

        self.connections: [Connection] = []

        self.client_auth_policy: Optional[TypeDict] = None


    def get_connection(self, connection_id):
        for connection in self.connections:
            if connection.connection_id == connection_id:
                return connection
        return None

    def _connections_handler(self, payload: TypeDict) -> None:
        state = payload["state"]
        connection_id = payload["connection_id"]
        their_role = payload["their_role"]
        routing_state = payload["routing_state"]

        print("----------------------------------------------------------")
        print("Connection Webhook Event Received")
        print("Connection ID : ", connection_id)
        print("State : ", state)
        print("Routing State : ", routing_state)
        print("Their Role : ", their_role)
        print("----------------------------------------------------------")
        loop = asyncio.get_event_loop()
        if state == "response":
            time.sleep(1)
            loop.run_until_complete(self.agent_controller.messaging.trust_ping(connection_id))
        elif state == "active":
            connection = self.get_connection(connection_id)
            if connection:
                print(f"Connection {connection_id} active.")
                connection.is_active.set_result(True)
                if connection.auth_policy:
                    print(f"Challenging connection {connection_id} with auth policy {connection.auth_policy['name']}")
                    # Specify the connection id to send the authentication request to
                    proof_request_web_request = {
                        "connection_id": connection_id,
                        "proof_request": connection.auth_policy,
                        "trace": False,
                    }
                    _ = loop.run_until_complete(
                        self.agent_controller.proofs.send_request(
                            proof_request_web_request
                        )
                    )
                else:
                    print(f"No authentication policy set for connection {connection_id}. Connection is set to trusted.")
                    connection.is_trusted.set_result(True)


    def _proof_handler(self, payload: TypeDict) -> None:
        role = payload["role"]
        connection_id = payload["connection_id"]
        pres_ex_id = payload["presentation_exchange_id"]
        state = payload["state"]
        print(
            "\n---------------------------------------------------------------------\n"
        )
        print("Handle present-proof")
        print("Connection ID : ", connection_id)
        print("Presentation Exchange ID : ", pres_ex_id)
        print("Protocol State : ", state)
        print("Agent Role : ", role)
        print(
            "\n---------------------------------------------------------------------\n"
        )
        if state == "presentation_received":
            # Only verify presentation's from pending scientist connections
            connection = self.get_connection(connection_id)
            if connection:
                loop = asyncio.get_event_loop()
                verification_response = loop.run_until_complete(
                    self.agent_controller.proofs.verify_presentation(pres_ex_id)
                )
                # Completing future with result of the verification - True of False
                if verification_response["verified"] == "true":
                    connection.is_trusted.set_result(True)
                    for (name, val) in verification_response['presentation']['requested_proof']['revealed_attrs'].items():
                        print("\nAttribute : ", val)

                        attr_name = verification_response["presentation_request"]["requested_attributes"][name]["name"]
                        connection.verified_attributes.append({"name": attr_name, "value": val['raw']})
                    for (name, val) in verification_response['presentation']['requested_proof']['self_attested_attrs'].items():
                        attr_name = verification_response["presentation_request"]["requested_attributes"][name]["name"]
                        connection.self_attested_attributes.append({"name": attr_name, "value": val})

                    print(f"Successfully verified presentation from connection {connection_id}. Connection now trusted.")


    def new_connection_invitation(self, proof_request: TypeDict = None, for_mobile: bool = False) -> TypeDict:

        loop = asyncio.get_event_loop()

        invitation_response = loop.run_until_complete(
            self.agent_controller.connections.create_invitation()
        )

        connection_id = invitation_response["connection_id"]

        new_connection = Connection(connection_id, auth_policy=proof_request)
        self.connections.append(new_connection)

        if for_mobile:
            # Link for connection invitation
            invitation_url = invitation_response["invitation_url"]
            return {"connection_id": connection_id, "invitation_url": invitation_url}
        else:
            json_invitation = invitation_response["invitation"]
            print("-" * 100)
            print(f"\nShare this invite object with another entity\n")
            print(json_invitation)
            print("\n")
            print("-" * 100)
            return {"connection_id": connection_id, "invitation": json_invitation}





    def connection_trusted(self, connection_id: str) -> bool:
        connection = self.get_connection(connection_id)
        return connection.is_trusted.done() and connection.is_trusted.result()


    def get_connections(self):
        return self.connections
