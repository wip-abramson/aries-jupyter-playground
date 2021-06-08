import json
from datetime import datetime
import asyncio
import nest_asyncio
from termcolor import colored
from .contact import Contact
from .message import Message

nest_asyncio.apply()

class MessagingService:
    
    def __init__(self, agent_controller):
        self.agent_controller = agent_controller
        self.contacts: list[Contact] = []
        self.save_file = "messaging-data.txt"
        listeners = [
            {
                "handler": self._messages_handler,
                "topic": "basicmessages"
            },
            {
                "handler": self._connections_handler,
                "topic": "connections"
            }
        ]
        
        self.agent_controller.register_listeners(listeners)
        
    
    def _messages_handler(self, payload):
        connection_id = payload["connection_id"]
        contact = self.find_contact_by_id(connection_id)
        if contact:
            print(f"Message received from connection {connection_id} with alias {contact.alias}")
            content = payload["content"]
            state = "received"
            
           
            contact.new_message(content, state)
    
    # Receive connection messages
    def _connections_handler(self, payload):
        state = payload['state']
        connection_id = payload["connection_id"]
        their_role = payload["their_role"]
        routing_state = payload["routing_state"]

#         if state == "invitation":
#             # Your business logic
#             print("invitation")
#         elif state == "request":
#             # Your business logic
#             print("request")

#         elif state == "response":
#             # Your business logic
#             print("response")
        if state == "active":
            their_label = payload["their_label"]
            contact = self.find_contact_by_id(connection_id)
            print(colored("Connection with ID: {0} is now active.".format(connection_id), "green", attrs=["bold"]))

            if contact:
                contact.is_active.set_result(True)
                contact.agent_label = their_label
                print(f"Contact {contact.alias} Added")
            else:
                print(f"No contact for active connection with ID {connection_id}")
                
            # Your business logic
            
        
    def find_contact_by_id(self, connection_id):
        for contact in self.contacts:
            if contact.connection_id == connection_id:
                return contact
        return None
    
    def display_inbox_for_contact(self, connection_id):
        contact = self.find_contact_by_id(connection_id)
        if not contact:
            print(f"No contact saved for connection with id {connection_id}")
            return
        print(contact.display_inbox())
    
    def view_inbox(self, show_inactive: bool = False):
        inbox_view = "-"* 50
        inbox_view += "\n"
        inbox_view += f"{len(self.contacts)} Contacts"
        inbox_view += "\n"
        inbox_view += "-"* 50
        inbox_view += "\n"
        for contact in self.contacts:
            if show_inactive:
                inbox_view += contact.display_view()
            elif contact.is_active.done() and contact.is_active.result():
                inbox_view += contact.display_view()
                
        print(inbox_view)
        
    def get_contacts(self):
        return self.contacts
    
    
    def send_message(self, connection_id, content):
        contact = self.find_contact_by_id(connection_id)
        if contact:
            if contact.is_active.done() and contact.is_active.result():
                state = "sent"
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.agent_controller.messaging.send_message(connection_id, content))
                contact.new_message(content, state)
            else:
                print(f"Contact {contact.alias} is not yet an active connection")
        else: 
            print(f"No contact saved for connection id {connection_id}")
        
    def add_contact(self, connection_id, alias):
        contact = Contact(connection_id, alias)
        print(f"Contact with ID {connection_id} and alias {alias} added")
        self.contacts.append(contact)
    
    def new_contact_invite(self, alias):
        auto_accept = "true"
        # Use public DID?
        public = "false"
        # Should this invitation be usable by multiple invitees?
        multi_use = "false"
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.agent_controller.connections.create_invitation(alias, auto_accept, public, multi_use))
        invitation = response["invitation"]
        connection_id = response["connection_id"]
        self.add_contact(connection_id, alias)
        json_invitation = json.dumps(invitation)
        
        print("-" * 100)
        print(f"\nShare this invite object with another entity you wish to add as a contact under alias {alias}\n")
        print(json_invitation)
        print("\n")
        print("-" * 100)
        return {"connection_id": connection_id, "invitation": json_invitation}
        
    
    def accept_contact_invitation(self, invitation, alias, label = None):
        loop = asyncio.get_event_loop()
        auto_accept="false"
        response = loop.run_until_complete(self.agent_controller.connections.receive_invitation(invitation,alias, auto_accept))
        connection_id = response["connection_id"]
        self.add_contact(connection_id, alias)

        
        # Endpoint you expect to recieve messages at
        my_endpoint = None

        accept_response = loop.run_until_complete(self.agent_controller.connections.accept_invitation(connection_id, label, my_endpoint))
        return connection_id

    
    def save_to_file(self):
        
        data = {}
        contacts = []
        
        for contact in self.contacts:
            if contact.is_active.done() and contact.is_active.result():
                inbox = []
                for message in contact.inbox:
                    
                    message_dict = message.__dict__
                    message_dict["time"] = message.time.isoformat()
                    inbox.append(message_dict)
                    
                contact_dict = contact.__dict__
                contact_dict["is_active"] = True
                contact_dict["inbox"] = inbox
                contacts.append(contact_dict)
        
                
            

        
        data["contacts"] = contacts
        
        print("Saved Contacts Data \n", data)
        with open(self.save_file, 'w') as outfile:
            json.dump(data, outfile)

    
    def load_from_file(self):

        with open(self.save_file) as json_file:
            data = json.load(json_file)
            
            for contact_dict in data["contacts"]:
                
                contact = Contact(contact_dict["connection_id"], contact_dict["alias"], contact_dict["agent_label"])
                
                contact.is_active.set_result(True)
                
                for message_dict in contact_dict["inbox"]:
                    
                    message = Message(message_dict["content"], message_dict["state"])
                    
                    message.time = datetime.fromisoformat(message_dict["time"])
                    
                    contact.inbox.append(message)
                
                self.contacts.append(contact)
        
        self.view_inbox()