import consul
import time
import socket
import threading
from requests.exceptions import RequestException

# Configuration
CONSUL_HOST = 'consul-server'
CONSUL_PORT = 8500
LOCK_KEY = 'service/leader'
TTL = '15s'  # Time-To-Live for the session

def create_session(client, name, ttl):
    """Create a new session in Consul with 'release' behavior."""
    try:
        session_id = client.session.create(name=name, behavior='release', ttl=ttl)
        print(f"Session created with ID: {session_id}")
        return session_id
    except RequestException as e:
        print(f"Failed to create session: {str(e)}")
        return None

def renew_session(client, session_id):
    """Renew the session."""
    while True:
        try:
            client.session.renew(session_id)
            print(f"Session {session_id} renewed successfully.")
            time.sleep(10)  # Renew session every 10 seconds
        except RequestException as e:
            print(f"Failed to renew session {session_id}: {str(e)}")
            break

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

    # Start a thread to renew the session
    renew_thread = threading.Thread(target=renew_session, args=(client, session_id))
    renew_thread.start()

    # Acquire the lock and perform leader tasks if successful
    if acquire_lock(client, session_id, LOCK_KEY):
        perform_leader_tasks()

    renew_thread.join()  # Wait for the renew thread to finish if it hasn't already

if __name__ == "__main__":
    main()
