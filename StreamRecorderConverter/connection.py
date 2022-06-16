import requests
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning
import base64
import warnings
import os
import io
import zipfile

warnings.simplefilter("ignore", InsecureRequestWarning)


def hex64(text: str):
    return base64.b64encode(text.encode("ascii")).decode("ascii")


class Auth:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.authentication = HTTPBasicAuth(username, password)


class WriteBytesFile:
    def __init__(self, content):
        self.content = content

    def save(self, filename):
        with open(filename, "wb") as f:
            f.write(self.content)


class WriteBytesFolder:
    def __init__(self, content):
        self.content = content

    def save(self, path=None, unzip=True):

        if not unzip and not path:
            raise ValueError("Must provide a path name for the zipped file being saved")

        if unzip:
            z = zipfile.ZipFile(io.BytesIO(self.content))
            z.extractall(path)
        else:
            with open(path, "wb") as f:
                f.write(self.content)


class DevicePortalBrowser:
    def __init__(self, ip: str, auth: Auth = None, verbose: bool = False):
        self.ip = ip
        self.auth = auth
        self.session = None
        self.base_url = f"https://{ip}"
        self.login_status = False
        self.verbose = verbose

        if self.verbose:
            print(" + Created a device portal interface")
            print("    - url: {}".format(self.base_url))
            if self.auth:
                print("    - user: {}".format(self.auth.username))
                print("    - pass: {}".format(self.auth.password))

    def reconnect(self):
        return self.connect()

    def connect(self):

        if self.verbose:
            print(" + Connecting to interface")
            print("    - Creating a session...")

        self.session = requests.Session()

        if self.verbose:
            print("    - Setting up auth and disabling verify")

        if self.auth:
            self.session.auth = self.auth.authentication

        self.session.verify = False

        if self.verbose:
            print("    - Connecting to url: {}".format(self.base_url))

        r = self.session.get(self.base_url)

        self.csrf_tok = self.session.cookies.get("CSRF-Token")

        if self.verbose:
            print(
                "    - Copying 'CSRF-Token' cookie to 'X-CSRF-Token' header with value: {}".format(
                    self.csrf_tok
                )
            )

        self.session.headers.update({"X-CSRF-Token": self.csrf_tok})
        self.login_status = r.status_code == 200

        if self.verbose:
            print(
                "    - Status: {}".format(
                    "Logged in" if self.login_status else "Failed to log in"
                )
            )

        return self

    def is_connected(self):
        return self.login_status

    def get(self, uri: str, *args, **kwargs):

        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")

        r = self.session.get(self.base_url + uri, *args, **kwargs)

        if self.verbose:
            print(" -> GET", r.url.replace(self.base_url, ""))
            print("    - Code: {}".format(r.status_code))

        return r

    def post(self, uri: str, *args, **kwargs):

        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")

        r = self.session.post(self.base_url + uri, *args, **kwargs)

        if self.verbose:
            print(" -> POST", r.url.replace(self.base_url, ""))
            print("    - Code: {}".format(r.status_code))

        return r

    def put(self, uri: str, *args, **kwargs):

        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")

        r = self.session.put(self.base_url + uri, *args, **kwargs)

        if self.verbose:
            print(" -> PUT", r.url.replace(self.base_url, ""))
            print("    - Code: {}".format(r.status_code))

        return r

    def delete(self, uri: str, *args, **kwargs):

        if not self.login_status:
            raise ValueError("DevicePortalBrowser not connected")

        r = self.session.delete(self.base_url + uri, *args, **kwargs)

        if self.verbose:
            print(" -> DELETE", r.url.replace(self.base_url, ""))
            print("    - Code: {}".format(r.status_code))

        return r


class HololensInterface(DevicePortalBrowser):
    def get_packages(self):
        resp = self.get("/api/app/packagemanager/packages")
        if resp:
            return resp.json()["InstalledPackages"]
        else:
            raise ValueError("Could not get packages")

    def get_processes(self):
        resp = self.get("/api/resourcemanager/processes")
        if resp:
            return resp.json()["Processes"]
        else:
            raise ValueError("Could not get processes")

    def start_app(self, package_full_name: str, package_relative_id: str):
        return self.post(
            "/api/taskmanager/app",
            params={
                "appid": hex64(package_relative_id),
                "package": hex64(package_full_name),
            },
        )

    def stop_app(self, package_full_name, forcestop=False):
        params = {"package": hex64(package_full_name)}
        if forcestop:
            params["forcestop"] = "yes"

        return self.delete("/api/taskmanager/app", params=params)

    def kill_process(self, pid: str):
        return self.delete("/api/taskmanager/process", params={"pid": pid})

    def get_known_folders(self):
        resp = self.get("/api/filesystem/apps/knownfolders")
        if resp:
            return resp.json()["KnownFolders"]
        else:
            raise ValueError("Could not get known folders")

    def get_files(
        self, known_folder: str, package_full_name: str = None, path: str = None
    ):
        params = {"knownfolderid": known_folder}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            p = os.path.normpath(path)
            p = p if p.startswith("\\") else "\\" + p
            params["path"] = p

        resp = self.get("/api/filesystem/apps/files", params=params)
        if resp:
            return resp.json()["Items"]
        else:
            raise ValueError("Could not get files")

    def download_file(
        self,
        known_folder: str,
        filename: str,
        package_full_name: str = None,
        path: str = None,
    ):
        params = {"knownfolderid": known_folder, "filename": filename}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            p = os.path.normpath(path)
            p = p if p.startswith("\\") else "\\" + p
            params["path"] = p

        resp = self.get("/api/filesystem/apps/file", params=params)
        if resp:
            return WriteBytesFile(resp.content)
        else:
            raise ValueError("Could not download file")

    def download_folder(
        self,
        known_folder: str,
        foldername: str,
        package_full_name: str = None,
        path: str = None,
    ):
        params = {"knownfolderid": known_folder, "filename": foldername}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            p = os.path.join(os.path.normpath(path), foldername)
            p = p if p.startswith("\\") else "\\" + p
            params["path"] = p

        resp = self.get("/api/filesystem/apps/folder", params=params)
        if resp:
            return WriteBytesFolder(resp.content)
        else:
            raise ValueError("Could not download folder")

    def delete_file(
        self,
        known_folder: str,
        filename: str,
        package_full_name: str = None,
        path: str = None,
    ):
        params = {"knownfolderid": known_folder, "filename": filename}
        if known_folder == "LocalAppData":
            params["packagefullname"] = package_full_name
        if path:
            p = os.path.normpath(path)
            p = p if p.startswith("\\") else "\\" + p
            params["path"] = p

        return self.delete("/api/filesystem/apps/file", params=params)
