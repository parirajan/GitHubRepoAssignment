import logging
import time
from systemd import dbus

def wait_for_service_active(service_name, timeout=60, check_interval=5):
    """
    Wait for a systemd service to become active.

    :param service_name: Name of the systemd service to check.
    :param timeout: Maximum time to wait for the service to become active, in seconds.
    :param check_interval: Time interval between status checks, in seconds.
    :return: True if the service becomes active, False if it times out.
    """
    try:
        # Connect to the D-Bus system bus
        system_bus = dbus.SystemBus()

        # Access the systemd interface
        systemd_manager = dbus.Interface(system_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'), 'org.freedesktop.systemd1.Manager')

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Get the service unit's object path
            service_unit_path = systemd_manager.GetUnit(f"{service_name}.service")

            # Access the service unit interface
            service_unit = dbus.Interface(system_bus.get_object('org.freedesktop.systemd1', service_unit_path), 'org.freedesktop.DBus.Properties')

            # Check the service's ActiveState property
            active_state = service_unit.Get('org.freedesktop.systemd1.Unit', 'ActiveState')

            if active_state == "active":
                logging.info(f"Service {service_name} is active.")
                return True

            time.sleep(check_interval)

        logging.warning(f"Timeout reached. Service {service_name} did not become active.")
        return False

    except Exception as e:
        logging.error(f"Error checking status of service {service_name}: {e}")
        return False

# Example usage
service_to_check = 'sshd'
is_active = wait_for_service_active(service_to_check, timeout=120, check_interval=10)
print(f"Service {service_to_check} active: {is_active}")
