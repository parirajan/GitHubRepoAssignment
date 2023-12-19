import logging
import time
from systemd import dbus

def wait_for_service_active(service_name, timeout=300, check_interval=10):
    """
    Wait in a loop until the specified systemd service is active or until timeout.

    Args:
    service_name (str): The name of the systemd service to check.
    timeout (int): Maximum time to wait for the service to become active, in seconds.
    check_interval (int): Interval between status checks, in seconds.
    """
    logging.basicConfig(level=logging.INFO)

    # Establish a connection to the systemd D-Bus
    bus = dbus.SystemBus()

    # Access the systemd1 manager interface
    systemd_manager = dbus.Interface(bus.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1"), 
                                     dbus_interface="org.freedesktop.systemd1.Manager")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            unit_path = systemd_manager.GetUnit(f"{service_name}.service")
            unit_proxy = bus.get_object("org.freedesktop.systemd1", unit_path)
            unit_properties = dbus.Interface(unit_proxy, dbus_interface='org.freedesktop.DBus.Properties')

            # Check the ActiveState property
            active_state = unit_properties.Get("org.freedesktop.systemd1.Unit", "ActiveState")
            
            if active_state == "active":
                logging.info(f"Service {service_name} is now active.")
                return True
            else:
                logging.info(f"Service {service_name} is not active. Checking again in {check_interval} seconds.")
                time.sleep(check_interval)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False

    logging.warning(f"Service {service_name} did not become active within {timeout} seconds.")
    return False

# Example usage
service_active = wait_for_service_active("your_service_name")
print("Service is active:", service_active)
