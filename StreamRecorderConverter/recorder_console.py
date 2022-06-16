import cmd
from pathlib import Path
from process_all import process_all

from connection import HololensInterface, Auth


class RecorderShell(cmd.Cmd):
    dev_portal_browser = None
    w_path = None

    # cmd variables
    intro = "Welcome to the recorder shell.   Type help or ? to list commands.\n"
    prompt = "(recorder console) "

    ruler = "-"

    def __init__(self, w_path, holo: HololensInterface):
        super().__init__()
        self.holo = holo
        self.w_path = w_path

        packages = holo.get_packages()
        self.package_full_name = None
        self.package_relative_id = None
        for package in packages:
            if package["Name"] == "StreamRecorder":
                self.package_full_name = package["PackageFullName"]
                self.package_relative_id = package["PackageRelativeId"]

        if self.package_full_name:
            print("[!] Found StreamRecorder:", self.package_full_name)
        else:
            raise ValueError("StreamRecorder not installed on device")

        self.do_list(None)

    def do_help(self, arg):
        print_help()

    def do_reconnect(self, arg):
        self.holo.reconnect()

    def do_exit(self, arg):
        return True

    def do_list(self, arg):
        print("Device recordings:")
        self.do_list_device(None)
        print("Workspace recordings:")
        list_workspace_recordings(self.w_path)

    def get_device_list(self):
        recordings = self.holo.get_files(
            "LocalAppData", self.package_full_name, "LocalState"
        )

        recording_names = []
        for r in recordings:
            files = self.holo.get_files(
                "LocalAppData", self.package_full_name, f"LocalState/{r['Id']}"
            )
            if len(files) > 0:
                recording_names.append(r["Id"])

        recording_names.sort()
        return recording_names

    def do_list_device(self, arg):

        recording_names = self.get_device_list()

        for i, recording_name in enumerate(recording_names):
            print("[{: 6d}]  {}".format(i, recording_name))
        if len(recording_names) == 0:
            print("=> No recordings found on Hololens")

    def do_list_workspace(self, arg):
        list_workspace_recordings(self.w_path)

    def download_recording(self, name):

        recording_path = self.w_path / name
        recording_path.mkdir(exist_ok=True)

        print("[!] Downloading recording {}...".format(name))

        files = self.holo.get_files(
            "LocalAppData", self.package_full_name, f"LocalState/{name}"
        )

        for file in files:
            if file["Type"] != 32:
                continue

            destination_path = recording_path / file["Id"]
            if destination_path.exists():
                print("[!] => Skipping, already downloaded:", file["Id"])
                continue

            print("    => Downloading:", file["Id"])
            self.holo.download_file(
                "LocalAppData", file["Id"], self.package_full_name, f"LocalState/{name}"
            ).save(destination_path)

    def delete_recording(self, name):

        print("[!] Deleting recording {}...".format(name))
        self.holo.delete_file(
            "LocalAppData", name, self.package_full_name, "LocalState"
        )

    def do_download(self, arg):
        try:
            recording_idx = int(arg)
            if recording_idx is not None:
                self.download_recording(self.get_device_list()[recording_idx])
        except ValueError:
            print(f"[!] I can't download {arg}")

    def do_download_all(self, arg):
        recordings = self.get_device_list()
        for record in recordings:
            self.download_recording(record)

    def do_delete_all(self, arg):
        recordings = self.get_device_list()
        for record in recordings:
            self.delete_recording(record)

    def do_delete(self, arg):
        try:
            recording_idx = int(arg)
            if recording_idx is not None:
                self.delete_recording(self.get_device_list()[recording_idx])
        except ValueError:
            print(f"[!] I can't delete {arg}")

    def do_process(self, arg):
        try:
            recording_idx = int(arg)
            if recording_idx is not None:
                try:
                    recording_names = sorted(self.w_path.glob("*"))
                    recording_name = recording_names[recording_idx]
                except IndexError:
                    print("[!] => Recording does not exist")
                else:
                    process_all(recording_name, True)
        except ValueError:
            print(f"[!] I can't extract {arg}")


def print_help():
    print("Available commands:")
    print("  help:                     Print this help message")
    print("  reconnect:                Reconnect to the device portal")
    print("  exit:                     Exit the console loop")
    print("  list:                     List all recordings")
    print("  list_device:              List all recordings on the HoloLens")
    print("  list_workspace:           List all recordings in the workspace")
    print("  download X:               Download recording X from the HoloLens")
    print("  download_all:             Download all recordings from the HoloLens")
    print("  delete X:                 Delete recording X from the HoloLens")
    print("  delete_all:               Delete all recordings from the HoloLens")
    print("  process X:                Process recording X ")


def list_workspace_recordings(w_path):
    recording_names = sorted(w_path.glob("*"))
    for i, recording_name in enumerate(recording_names):
        print("[{: 6d}]  {}".format(i, recording_name.name))
    if len(recording_names) == 0:
        print("    => No recordings found in workspace")


def main():

    address = "10.0.0.208"  # change to the ip for your hololens device portal
    login = Auth(
        "admin22", "admin22"
    )  # set to None if no username and password is requred
    w_path = Path(
        "downloads"
    )  # set to desired download folder path

    w_path.mkdir(exist_ok=True)
    holo = HololensInterface(address, auth=login).connect()

    print()
    print_help()
    print()

    rs = RecorderShell(w_path, holo)
    rs.cmdloop()


if __name__ == "__main__":
    main()
