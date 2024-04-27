import consul
import time
import socket
from requests.exceptions import RequestException

# Configuration
CONSUL_HOST = 'consul-server'
CONSUL_PORT = 8500
LOCK_KEY = 'service/leader'
TTL = '15s'  # Time-To-Live for the session

def create_session(client, name, ttl):
    """Create a new session in Consul."""
    try:
        session_id = client.session.create(name=name, behavior='delete', ttl=ttl)
        print(f"Session created with ID: {session_id}")
    except RequestException as e:
        print(f"Failed to create session: {str(e)}")
        session_id = None
    return session_id

def renew_session(client, session_id):
    """Renew the session."""
    try:
        client.session.renew(session_id)
        print(f"Session {session_id} renewed successfully.")
        return True
    except RequestException as e:
        print(f"Failed to renew session {session_id}: {str(e)}")
        return False

def acquire_lock(client, session_id, lock_key):
    """Attempt to acquire the lock."""
    try:
        if client.kv.put(lock_key, socket.gethostname(), acquire=session_id):
            print(f"Lock acquired by {socket.gethostname()}")
            return True
        else:
            print("Lock acquisition failed.")
            return False
    except RequestException as e:
        print(f"Error acquiring lock: {str(e)}")
        return False

def release_lock(client, session_id, lock_key):
    """Release the lock and destroy the session."""
    try:
        client.kv.put(lock_key, release=session_id)
        client.session.destroy(session_id)
        print("Lock released and session destroyed")
    except RequestException as e:
        print(f"Error releasing lock or destroying session: {str(e)}")

def perform_leader_tasks():
    """Perform tasks exclusive to the leader."""
    try:
        while True:
            print(f"Leader {socket.gethostname()} is active")
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
        # Acquire lock and perform leader tasks
        if acquire_lock(client, session_id, LOCK_KEY):
            perform_leader_tasks()
        # Continuously check if the session needs to be renewed or lock re-acquired
        while True:
            if not renew_session(client, session_id):
                break
            time.sleep(10)
    finally:
        release_lock(client, session_id, LOCK_KEY)

if __name__ == "__main__":
    main()
