import json
from datetime import datetime
import asyncio
import nest_asyncio
from termcolor import colored

nest_asyncio.apply()

class MessagingService:
    
    def __init__(self, agent_controller):
        self.agent_controller = agent_controller
        self.contacts: list[Contact] = []
        
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
            if contact:
                contact.is_active.set_result(True)
                contact.agent_label = their_label
                print(colored("Contact with ID: {0} and alias {1} is now active.".format(connection_id, contact.alias), "green", attrs=["bold"]))
            else:
                print(f"No contact for active connection with ID {connection_id}")
                
            # Your business logic
            
        
    def find_contact_by_id(self, connection_id):
        contact_exists = False
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
            if not contact.is_active and show_inactive:
                inbox_view += contact.display_view()
            elif contact.is_active:
                inbox_view += contact.display_view()
                
        print(inbox_view)
        
    def get_contacts(self):
        return self.contacts
    
    
    def send_message(self, connection_id, content):
        contact = self.find_contact_by_id(connection_id)
        if contact:
            if contact.is_active:
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


class Contact:
    
    def __init__(self, connection_id, alias, agent_label = None):
        self.connection_id = connection_id
        self.alias = alias
        self.agent_label = None
        self.inbox = []
        self.is_active = asyncio.Future()
        
    def new_message(self, content, state):
        message = Message(content, state)
        self.inbox.append(message)
        
    def display_view(self):
            view = f"Contact {self.alias}\nID: {self.connection_id} \nLabel: {self.agent_label}\n"
            if self.is_active:
                status = "ACTIVE"
            else:
                status = "INACTIVE"
            view += f"Status : {status} \n"
            view += f"Messages {len(self.inbox)} \n"
            view += "-"* 50
            view += "\n"
            return view
        
    def display_inbox(self):
        inbox_str = "-"*50
        inbox_str += "\n"
        inbox_str += f"Inbox for Contact {self.alias} \n"
        
        inbox_str += "\n"
        inbox_str += "-"*50
        inbox_str += "\n"
        inbox_str += f"Connection ID : {self.connection_id} \nAgent Label : {self.agent_label} \nTotal Messages : {len(self.inbox)}"
        inbox_str += "\n\n"
        inbox_str += "-"*50
        for message in self.inbox:
            inbox_str += "\n"
            inbox_str += message.to_string()
        return inbox_str
    
    
class Message:

    def __init__(self, content, state):
        self.content = content
        self.state = state
        self.time = datetime.now()
        
    def to_string(self):
        msg_str = self.time.strftime("%c")
        n = 25
        words = self.content.split()
        
        msg_chunks = [self.content[i:i+n] for i in range(0, len(self.content), n)]
        line_start = ""
        if self.state == "sent":
            line_start += (" "*25)
        current_line = ""
        for word in words:
            current_line += (word + " ")
            if len(current_line) > 25:
                msg_str += "\n"
                msg_str += (line_start + current_line)
                current_line = ""
        if not current_line == "":
            msg_str += "\n"
            msg_str += (line_start + current_line)
        msg_str += "\n"
        msg_str += ("-"*50)
        return msg_str