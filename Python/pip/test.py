import logging
import time
import subprocess

def wait_for_service_active(service_name, timeout=300, check_interval=10):
    """
    Wait in a loop until the specified systemd service is active or until timeout.

    Args:
    service_name (str): The name of the systemd service to check.
    timeout (int): Maximum time to wait for the service to become active, in seconds.
    check_interval (int): Interval between status checks, in seconds.
    """
    logging.basicConfig(level=logging.INFO)

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Use systemctl to check the service status
            result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
            if result.stdout.strip() == "active":
                logging.info(f"Service {service_name} is now active.")
                return True
            else:
                logging.info(f"Service {service_name} is not active. Checking again in {check_interval} seconds.")
        except Exception as e:
            logging.error(f"An error occurred while checking the service status: {e}")
            return False

        time.sleep(check_interval)

    logging.warning(f"Service {service_name} did not become active within {timeout} seconds.")
    return False

# Example usage
service_active = wait_for_service_active("your_service_name.service")
print("Service is active:", service_active)
