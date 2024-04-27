import consul
import time
import socket
from requests.exceptions import RequestException

# Configuration
CONSUL_HOST = 'consul-server'
CONSUL_PORT = 8500
LOCK_KEY = 'service/leader'
TTL = '15s'

def create_session(client, name, ttl):
    session_id = None
    try:
        session_id = client.session.create(name=name, behavior='delete', ttl=ttl)
        print(f"Session created with ID: {session_id}")
    except RequestException as e:
        print(f"Failed to create session: {str(e)}")
    return session_id

def renew_session(client, session_id):
    try:
        client.session.renew(session_id)
        print(f"Session {session_id} renewed successfully.")
    except RequestException as e:
        print(f"Failed to renew session {session_id}: {str(e)}")
        return False
    return True

def acquire_lock(client, session_id, lock_key):
    index, data = client.kv.get(lock_key)
    if data and data['Session'] == session_id:
        # Already have the lock
        return True
    if client.kv.put(lock_key, socket.gethostname(), acquire=session_id):
        print(f"Lock acquired by {socket.gethostname()}")
        return True
    return False

def release_lock(client, session_id, lock_key):
    client.kv.put(lock_key, release=session_id)
    client.session.destroy(session_id)
    print("Lock released and session destroyed")

def perform_leader_tasks():
    """Simulate leader work."""
    try:
        while True:
            print(f"{socket.gethostname()} is leading...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping leader tasks...")

def main():
    client = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    
    # Create a new session
    session_id = create_session(client, "Leader Election", TTL)
    if not session_id:
        return

    try:
        while True:
            if acquire_lock(client, session_id, LOCK_KEY):
                perform_leader_tasks()
            if not renew_session(client, session_id):
                break
            time.sleep(5)
    finally:
        release_lock(client, session_id, LOCK_KEY)

if __name__ == "__main__":
    main()
