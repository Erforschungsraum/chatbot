import os

def sync_with_github():
    print("Projekt wird mit GitHub synchronisiert...")

    # Git-Befehle ausführen
    os.system("git add .")
    os.system('git commit -m "Automatischer Commit"')
    os.system("git push")

    print("Projekt erfolgreich mit GitHub synchronisiert!")


def ask_version_update():
    with open("version.txt", "r") as file:
        version = file.read().strip()

    print(f"Aktuelle Version: {version}")
    print("Möchtest du die Version erhöhen?")
    print("1 - Minor erhöhen")
    print("2 - Major erhöhen")
    print("3 - Keine Änderungen")

    choice = input("Wähle aus (1/2/3): ")

    major, minor, patch = map(int, version.split("."))

    if choice == "1":
        minor += 1
        patch = 0
    elif choice == "2":
        major += 1
        minor = 0
        patch = 0
    elif choice == "3":
        print("Keine Änderungen an der Version vorgenommen.")
        return

    new_version = f"{major:02}.{minor:02}.{patch:04}"
    with open("version.txt", "w") as file:
        file.write(new_version)

    print(f"Neue Version: {new_version}")


if __name__ == "__main__":
    ask_version_update()
    sync_with_github()
