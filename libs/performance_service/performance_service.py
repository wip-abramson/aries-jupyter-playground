import time
import asyncio
import nest_asyncio
from termcolor import colored
nest_asyncio.apply()
import json

class PerformanceService:

    def __init__(self, agent_controller, iterations: int = 100):
        self.iterations = iterations
        self.agent_controller = agent_controller

        self.agent_listeners = [
            {"topic": "issue_credential", "handler": self._issuer_handler},
            {"topic": "present_proof", "handler": self._verifier_handler},
            {"topic": "connections", "handler": self._connections_handler},
        ]
        self.agent_controller.register_listeners(self.agent_listeners, defaults=True)

        self.experiments = []
        self.timing_future = None

    def new_experiment(self, name):
        experiment = {"name": name, "results": []}
        self.experiments.append(experiment)
        return experiment

    async def run_issuance(self, experiment, test, connection_id):

        result = {"name" : test["name"], "timings": []}


        schema_id = test['schema_id']
        cred_def_id = test['cred_def_id']
        attributes = test['attributes']
        sum = 0
        for x in range(self.iterations):
            self.timing_future = asyncio.Future()
            start_time = time.perf_counter()
            await self.agent_controller.issuer.send_credential(connection_id, schema_id, cred_def_id, attributes)

            await self.timing_future
            elapsed_time = time.perf_counter() - start_time
            result["timings"].append(elapsed_time)
            sum += elapsed_time

            # print(f"Elapsed time: {elapsed_time:0.5f} seconds")

        average = sum / self.iterations
        # print("Timings : ", result["timings"])
        print("Average : ", average)

        result["average"] = average

        experiment["results"].append(result)


    async def run_verification(self, experiment, test, connection_id):
        result = {"name" : test["name"], "timings": []}

        proof_request_json = {
            "comment": "some optional comment",
            "connection_id": connection_id,
            "proof_request": test["proof_request"],
            # Do you want your agent to trace this request (for debugging)
            "trace": False
        }
        sum = 0
        for x in range(self.iterations):
            self.timing_future = asyncio.Future()
            start_time = time.perf_counter()
            await self.agent_controller.proofs.send_request(proof_request_json)

            await self.timing_future
            elapsed_time = time.perf_counter() - start_time
            result["timings"].append(elapsed_time)
            sum += elapsed_time

        average = sum / self.iterations
        # print("Timings : ", result["timings"])
        print("Average : ", average)

        result["average"] = average

        experiment["results"].append(result)


    def save_experiments(self):
        for experiment in self.experiments:

            file_name = experiment["name"] + ".txt"

            with open(file_name, 'w') as outfile:
                json.dump(experiment, outfile)





    def load_experiment_from_file(self, file_name):

        with open(file_name) as json_file:
            data = json.load(json_file)
            self.experiments.append(data)




    def _verifier_handler(self, payload):
        state = payload['state']

        if state == "verified":
            self.timing_future.set_result(True)


    def _issuer_handler(self, payload):
        state = payload['state']
            ## YOUR LOGIC HERE
        if state == "credential_acked":
            # print(self.issuance_future)
            self.timing_future.set_result(True)

    def _connections_handler(self, payload):
        state = payload['state']
        connection_id = payload["connection_id"]
        their_role = payload["their_role"]
        routing_state = payload["routing_state"]

        if state == "active":
            # Your business logic
            print(colored("Connection ID: {0} is now active.".format(connection_id), "green", attrs=["bold"]))