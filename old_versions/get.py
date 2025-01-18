import dbus
import dbus.mainloop.glib
from gi.repository import GLib

def on_message_received(message_id, sender, group_id, body, extras):
    """
    Callback, wenn eine Nachricht empfangen wird.

    :param message_id: ID der Nachricht
    :param sender: Telefonnummer des Absenders
    :param sender_name: Anzeigename des Absenders
    :param group_id: ID der Gruppe, falls es sich um eine Gruppennachricht handelt
    :param timestamp: Zeitstempel der Nachricht
    :param extras: Zusätzliche Metadaten
    """
    print("Nachricht empfangen!")
    print(f"Nachricht ID: {message_id}")
    print(f"Absender: {sender}")
    print(f"Gruppe: {group_id}")
    print(f"Body: {body}")
    print(f"Zusatzinformationen: {extras}")

def main():
    # DBus Initialisierung
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    # Abonniere das Signal
    bus.add_signal_receiver(
        handler_function=on_message_received,
        dbus_interface="org.asamk.Signal",
        signal_name="MessageReceivedV2"
    )

    print("Warte auf eingehende Nachrichten...")
    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()
