import asyncio
from .message import Message


class Contact:
    
    def __init__(self, connection_id, alias, agent_label = None):
        self.connection_id = connection_id
        self.alias = alias
        self.agent_label = None
        self.inbox: [Message] = []
        self.is_active = asyncio.Future()
        
    def new_message(self, content, state):
        message = Message(content, state)
        self.inbox.append(message)
        
    def display_view(self):
            view = f"Contact {self.alias}\nID: {self.connection_id} \nLabel: {self.agent_label}\n"
            try:
                active = self.is_active.result()
                if active:
                    status = "ACTIVE"
                else: 
                    status = "INACTIVE"
            except:
                status = "INACTIVE"
            view += f"Status : {status} \n"
            view += f"Messages {len(self.inbox)} \n"
            view += "-"* 50
            view += "\n"
            return view
        
    def display_inbox(self):
        inbox_str = "-"*50
        inbox_str += "\n"
        inbox_str += f"Inbox for Contact {self.alias}"
        
        inbox_str += "\n"
        inbox_str += "-"*50
        inbox_str += "\n"
        inbox_str += f"Connection ID : {self.connection_id} \nAgent Label : {self.agent_label} \nTotal Messages : {len(self.inbox)}"
        inbox_str += "\n"
        inbox_str += "-"*50
        inbox_str += "\n"
        inbox_str += "Received" + " "*38 + "Sent"
        inbox_str += "\n"
        inbox_str += "-"*50
        for message in self.inbox:
            inbox_str += "\n"
            inbox_str += message.to_string()
        return inbox_str