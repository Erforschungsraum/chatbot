import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class SaveEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("signal_chatbot.py"):
            print(f"{event.src_path} wurde gespeichert. Version wird erhöht...")
            increment_version()


def increment_version():
    version_file = "version.txt"

    # Version laden
    with open(version_file, "r") as file:
        version = file.read().strip()

    major, minor, patch = map(int, version.split("."))

    # Patch erhöhen
    patch += 1
    if patch >= 10000:  # Beispiel: Patch-Zähler zurücksetzen
        patch = 0
        minor += 1

    new_version = f"{major:02}.{minor:02}.{patch:04}"

    # Version speichern
    with open(version_file, "w") as file:
        file.write(new_version)

    print(f"Neue Version: {new_version}")


if __name__ == "__main__":
    path = "."
    event_handler = SaveEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    print("Beobachte Änderungen im Projektverzeichnis...")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
