import requests
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning
import base64
import warnings
import json
import os

warnings.simplefilter("ignore", InsecureRequestWarning)

def hex64(text: str):
    return base64.b64encode(text.encode("ascii")).decode("ascii")

class DevicePortalBrowser:
    
    def __init__(self, ip: str, username: str, password: str, verbose: bool = False):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None
        self.base_url = f"https://{ip}"
        self.login_status = False
        self.verbose = verbose
        
        if self.verbose:
            print(" + Created a device portal interface")
            print("    - url: {}".format(self.base_url))
            print("    - user: {}".format(username))
            print("    - pass: {}".format(password))
    
    def reconnect(self):
        return self.connect()
    
    def connect(self):
        
        if self.verbose:
            print(" + Connecting to interface")
            print("    - Creating a session...")
        
        self.session = requests.Session()
        
        if self.verbose:
            print("    - Setting up auth and disabling verify")
        
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.verify = False
        
        if self.verbose:
            print("    - Connecting to url: {}".format(self.base_url))
        
        r = self.session.get(self.base_url)
        
        self.csrf_tok = self.session.cookies.get("CSRF-Token")
        
        if self.verbose:
            print("    - Copying 'CSRF-Token' cookie to 'X-CSRF-Token' header with value: {}".format(self.csrf_tok))
        
        self.session.headers.update({"X-CSRF-Token": self.csrf_tok})
        self.login_status = r.status_code == 200
        
        if self.verbose:
            print("    - Status: {}".format("Logged in" if self.login_status else "Failed to log in"))
        
        return self
        
    def is_connected(self):
        return self.login_status
        
    def get(self, uri: str, *args, **kwargs):
        
        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")
        
        r = self.session.get(self.base_url + uri, *args, **kwargs)
        
        if self.verbose:
            print(" -> GET", r.url.replace(self.base_url, ''))
            print("    - Code: {}".format(r.status_code))
        
        return r
        
    def post(self, uri: str, *args, **kwargs):
        
        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")
        
        r = self.session.post(self.base_url + uri, *args, **kwargs)
        
        if self.verbose:
            print(" -> POST", r.url.replace(self.base_url, ''))
            print("    - Code: {}".format(r.status_code))
        
        return r
    
    def put(self, uri: str, *args, **kwargs):
        
        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")
        
        r = self.session.put(self.base_url + uri, *args, **kwargs)
        
        if self.verbose:
            print(" -> PUT", r.url.replace(self.base_url, ''))
            print("    - Code: {}".format(r.status_code))
        
        return r
    
    def delete(self, uri: str, *args, **kwargs):
        
        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")
        
        r = self.session.delete(self.base_url + uri, *args, **kwargs)
        
        if self.verbose:
            print(" -> DELETE", r.url.replace(self.base_url, ''))
            print("    - Code: {}".format(r.status_code))
        
        return r


class HololensInterface(DevicePortalBrowser):
    
    def install_app(self, package: str, body):
        return self.post("/api/app/packagemanager/package", params={"package": package}, data=body)
    
    def register_app_loose_folder(self, path: str, user_pass: tuple[str, 2] = None):
        to_dump = {"mainpackage":{"networkshare": path}}
        if user_pass:
            to_dump["mainpackage"]["username"], to_dump["mainpackage"]["password"] = user_pass
            
        return self.post("/api/app/packagemanager/package", json=json.dumps(to_dump))
    
    def get_app_installation_status(self):
        return self.get("/api/app/packagemanager/state")
    
    def uninstall_app(self, package_full_name: str):
        return self.delete("/api/app/packagemanager/package", params={"package": package_full_name})
    
    def get_installed_apps(self):
        return self.get("/api/app/packagemanager/packages")
    
    def get_bluetooth_radios(self):
        return self.get("/api/bt/getradios")
    
    def set_bluetooth_radio_state(self, id: str, state: bool):
        return self.post("/api/bt/setradio", params={"ID": hex64(id), "State": "On" if state else "Off"})
    
    def get_bluetooth_paired_devices(self):
        return self.get("/api/bt/getpaired")
    
    def get_available_bluetooth_devices(self):
        return self.get("/api/bt/getavailable")
    
    def connect_bluetooth_device(self, id: str):
        return self.post("/api/bt/connectdevice", params={"ID": hex64(id)})
    
    def disconnect_bluetooth_device(self, id: str):
        return self.post("/api/bt/disconnectdevice", params={"ID": hex64(id)})
    
    def get_app_crash_dumps(self):
        return self.get("/api/debug/dump/usermode/dumps")
    
    def get_app_crash_dump_collection_status(self, package_full_name: str):
        return self.get("/api/debug/dump/usermode/crashcontrol", params={"packageFullname": package_full_name})
    
    def delete_sideloaded_app_crash_dump(self, package_full_name: str, file: str):
        return self.delete("/api/debug/dump/usermode/crashdump", params={"packageFullname": package_full_name, "fileName": file})
    
    def disable_sideloaded_app_crash_dumps(self, package_full_name: str):
        return self.delete("/api/debug/dump/usermode/crashcontrol", params={"packageFullname": package_full_name})
    
    def download_sideloaded_app_crash_dump(self, package_full_name: str, file: str):
        return self.get("/api/debug/dump/usermode/crashdump", params={"packageFullname": package_full_name, "fileName": file})
    
    def enable_sideloaded_app_crash_dumps(self, package_full_name: str):
        return self.post("/api/debug/dump/usermode/crashcontrol", params={"packageFullname": package_full_name})
    
    def enumerate_registered_ETW_providers(self):
        return self.get("/api/etw/providers")
    
    def enumerate_custom_ETW_providers(self):
        return self.get("/api/etw/customproviders")
    
    def get_location_override_mode(self):
        return self.get("/ext/location/override")
    
    def set_location_override_mode(self, mode: bool):
        return self.put("/ext/location/override", json=json.dumps({"Override": mode}))
    
    def get_injected_position(self):
        return self.get("/ext/location/position")
    
    def set_injected_position(self, latitude: float, longitude: float):
        return self.put("/ext/location/override", json=json.dumps({"Latitude": latitude, "Longitude": longitude}))
    
    def get_machine_name(self):
        return self.get("/api/os/machinename")
    
    def get_os_information(self):
        return self.get("/api/os/info")
    
    def get_device_family(self):
        return self.get("/api/os/devicefamily")
    
    def set_machine_name(self, name: str):
        return self.post("/api/os/machinename", params={"name": hex64(name)})
    
    def get_active_user(self):
        return self.get("/api/users/activeuser")
    
    def get_running_processes(self):
        return self.get("/api/resourcemanager/processes")
    
    def get_system_performance_statistics(self):
        return self.get("/api/resourcemanager/systemperf")
    
    def get_current_battery_state(self):
        return self.get("/api/power/battery")
    
    def get_system_power_state(self):
        return self.get("/api/power/state")
    
    def restart_computer(self):
        return self.post("/api/control/restart")
    
    def shutdown_computer(self):
        return self.post("/api/control/shutdown")
    
    def start_modern_app(self, package_full_name: str, package_relative_id: str):
        return self.post("/api/taskmanager/app", params={"appid": hex64(package_relative_id), "package": hex64(package_full_name)})
    
    def stop_modern_app(self, package_full_name, forcestop=False):
        params = {"package": hex64(package_full_name)}
        if forcestop:
            params["forcestop"] = "yes"
        
        return self.delete("/api/taskmanager/app", params=params)
    
    def kill_process(self, pid: str):
        return self.delete("/api/taskmanager/process", params={"pid": pid})
    
    def get_current_ip_configuration(self):
        return self.get("/api/networking/ipconfig")
    
    def set_ipv4_static_ip_address(self, adapter_name: str, ip_address: str, subnet_mask: str, default_gateway: str, primary_dns: str, secondary_dns: str):
        return self.put("/api/networking/ipv4config", params={
            "AdapterName": adapter_name,
            "IPAddress": ip_address,
            "SubnetMask": subnet_mask,
            "DefaultGateway": default_gateway,
            "PrimaryDNS": primary_dns,
            "SecondaryDNS": secondary_dns})
        
    def enumerate_wireless_network_interfaces(self):
        return self.get("/api/wifi/interfaces")
    
    def enumerate_wireless_networks(self):
        return self.get("/api/wifi/networks")
    
    def connect_to_wifi_network(self, interface_guid: str, ssid: str, key: str = None, create_profile: bool = True):
        params = {"interface": interface_guid, "op": "connect", "ssid": ssid, "createprofile": "yes" if create_profile else "no"}
        if key:
            params["key"] = key
        return self.post("/api/wifi/network", params=params)
    
    def disconnect_from_wifi_network(self, interface_guid: str):
        return self.post("/api/wifi/network", params={"interface": interface_guid, "op": "disconnect"})
    
    def delete_wifi_profile(self, interface_guid: str, profile_name: str):
        return self.delete("/api/wifi/profile", params={"interface": interface_guid, "profile": profile_name})
    
    def download_windows_error_reporting_file(self, user: str, type: str, name: str, file: str):
        return self.get("/api/wer/report/file", params={"user": user, "type": type, "name": hex64(name), "file": hex64(file)})
    
    def enumerate_windows_error_reporting_report(self, user: str, type: str, name: str):
        return self.get("/api/wer/report/files", params={"user": user, "type": type, name: hex64(name)})
    
    def get_windows_error_reporting_reports(self):
        return self.get("/api/wer/reports")
    
    def start_tracing_with_custom_profile(self, body):
        return self.post("/api/wpr/customtrace", data=body)
    
    def start_boot_performance_tracing_session(self, profile: str):
        return self.post("/api/wpr/boottrace", params={"profile": profile})
    
    def stop_boot_performance_tracing_session(self):
        return self.get("/api/wpr/boottrace")
    
    def start_performance_tracing_session(self, profile: str):
        return self.post("/api/wpr/trace", params={"profile": profile})
    
    def stop_performance_tracing_session(self):
        return self.get("/api/wpr/trace")
    
    def get_tracing_session_status(self):
        return self.get("/api/wpr/status")
    
    def get_completed_tracing_sessions(self):
        return self.get("/api/wpr/tracefiles")
    
    def download_tracing_session(self, filename: str):
        return self.get("/api/wpr/tracefile", params={"filename": filename})
    
    def delete_tracing_session(self, filename: str):
        return self.delete("/api/wpr/tracefile", params={"filename": filename})
    
    def get_dns_sd_tags(self):
        return self.get("/api/dns-sd/tags")
    
    def delete_all_dns_sd_tags(self):
        return self.delete("/api/dns-sd/tags")
    
    def delete_dns_sd_tag(self, tag_value: str):
        return self.delete("/api/dns-sd/tag", params={"tagValue": tag_value})
    
    def add_dns_sd_tag(self, tag_value: str):
        return self.post("/api/dns-sd/tag", params={"tagValue": tag_value})
    
    def get_known_folders(self):
        return self.get("/api/filesystem/apps/knownfolders")
    
    def get_files_in_folder(self, known_folder: str, package_full_name: str = None, path: str = None):
        params = {"knownfolderid": known_folder}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            params["path"] = path
        
        return self.get("/api/filesystem/apps/files", params=params)
    
    def download_file(self, known_folder: str, filename: str, package_full_name: str = None, path: str = None):
        params = {"knownfolderid": known_folder, "filename": filename}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            params["path"] = path
            
        return self.get("/api/filesystem/apps/file", params=params)
    
    def rename_file(self, known_folder: str, filename: str, newfilename: str, package_full_name: str = None, path: str = None):
        params = {"knownfolderid": known_folder, "filename": filename, "newfilename": newfilename}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            params["path"] = path
            
        return self.post("/api/filesystem/apps/rename", params=params)
    
    def delete_file(self, known_folder: str, filename: str, package_full_name: str = None, path: str = None):
        params = {"knownfolderid": known_folder, "filename": filename}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            params["path"] = path
            
        return self.delete("/api/filesystem/apps/file", params=params)
    
    def upload_file(self, known_folder: str, file: str, extract: bool, package_full_name: str = None, path: str = None):
        params = {"knownfolderid": known_folder, "extract": extract}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            params["path"] = path
        
        return self.post("/api/filesystem/apps/file", params=params, files={os.path.basename(file): open(file, "rb")})


holo = HololensInterface("10.0.0.208", "admin22", "admin22", True).connect()
print(holo.get_known_folders().json())