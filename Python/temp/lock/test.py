import consul
import time
import os
import uuid

class LeaderElector:
    def __init__(self, consul_host, consul_port, key_name):
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.session_id = None
        self.key_name = key_name
        self.is_leader = False

    def create_session(self):
        session_name = f"session_{uuid.uuid4()}"
        self.session_id = self.consul.session.create(name=session_name, behavior='delete', ttl=15)
        print(f"Created session {session_name} with ID {self.session_id}")

    def acquire_lock(self):
        print("Attempting to acquire lock...")
        self.is_leader = self.consul.kv.put(self.key_name, 'leader', acquire=self.session_id)
        if self.is_leader:
            print("Lock acquired. This node is the leader.")
        else:
            print("Lock not acquired. This node is a follower.")

    def release_lock(self):
        if self.is_leader:
            self.consul.kv.put(self.key_name, '', release=self.session_id)
            print("Lock released.")

    def renew_session(self):
        if self.is_leader:
            self.consul.session.renew(self.session_id)
            print("Session renewed.")

    def run_leader_task(self):
        if self.is_leader:
            print("Running leader task...")
            counter = 0
            try:
                while True:
                    counter += 1
                    print(f"Leader task running... Current count: {counter}")
                    time.sleep(1)  # Sleep for 1 second to slow down the output
            except KeyboardInterrupt:
                print("Leader task interrupted.")
            except Exception as e:
                print(f"Error during leader task: {e}")


    def step_down(self):
        self.release_lock()
        self.consul.session.destroy(self.session_id)
        print("Stepped down from leadership.")

    def elect_leader(self):
        self.create_session()
        while True:
            self.acquire_lock()
            if self.is_leader:
                try:
                    self.run_leader_task()
                except Exception as e:
                    print(f"Error during leader task: {e}")
                    self.step_down()
                break
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    leader_elector = LeaderElector('localhost', 8500, 'service/leader')
    try:
        leader_elector.elect_leader()
    except KeyboardInterrupt:
        leader_elector.step_down()
