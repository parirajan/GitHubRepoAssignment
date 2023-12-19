import logging
import time
import subprocess

def is_service_active(service_name):
    """
    Check if the specified systemd service is active using systemctl.

    Args:
    service_name (str): The name of the systemd service to check.

    Returns:
    bool: True if the service is active, False otherwise.
    """
    try:
        # Use systemctl to check the service status
        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
        return result.stdout.strip() == "active"
    except Exception as e:
        logging.error(f"An error occurred while checking the service status: {e}")
        return False

def wait_for_service(service_name, timeout=300):
    """
    Wait in a loop until the specified systemd service is active or until timeout.

    Args:
    service_name (str): The name of the systemd service to check.
    timeout (int): Maximum time to wait for the service to become active, in seconds.
    """
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_service_active(service_name):
            logging.info(f"Service {service_name} is now active.")
            return
        else:
            logging.info(f"Service {service_name} is not active. Checking again in 10 seconds.")
            time.sleep(10)

    logging.warning(f"Service {service_name} did not become active within {timeout} seconds.")

# Example usage
wait_for_service("your_service_name.service")
