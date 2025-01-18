import subprocess
import json
import time
import os
import sys
import logging
import pymysql
from datetime import datetime
import traceback
from dotenv import load_dotenv
import os

load_dotenv() # Laden der Umgebungsvariablen aus der .env-Datei //selbst anlegen



print("\n\n\n\nStarte Chatbot...")
# --- Konfigurationen und eigenschaften des Bots ---
# Liste der Befehle, die der Bot ausführen kann

"""modi_prototype = {
    "name": "string",  # Der Name des Moduls (eine beschreibende Zeichenkette)
    "status_condition": lambda status: bool (bspw. bool => status >= 2, ),  # Eine Bedingung, die prüft, ob das Modul für einen bestimmten Status aktiv ist
    "trigger_words": ["string", "*"],  # Eine Liste von Schlüsselwörtern, die das Modul auslösen (oder "*" für alle Wörter)
    "trigger_groups": ["groupname", "*"],  # (Optional) Gruppen, die das Modul auslösen (oder "*" für alle Gruppen)
    "trigger_actions": ["string"],  # Eine Liste von Aktionen, die das Modul auslösen, z. B. "WRITE", "JOIN"
    "function": "string",  # Der Name der Funktion, die aufgerufen wird, wenn die Bedingung erfüllt ist
}"""

modis = [
    {
        "name": "Wegweiser für Eingangsbereich",
        "status_condition": lambda status: status <= 1,  # Für Benutzer mit Status < 1
        "trigger_words": ["*"],  # "*" bedeutet jede Nachricht
        "trigger_actions": ["WRITE"],  # Aktionen, die den Befehl auslösen
        "function": "send_wegweiser"
    },
    {
        "name": "Willkommensnachricht",
        "status_condition": lambda status: status <= 1,  # Für Benutzer mit Status < 1
        "trigger_groups": ["Empfang 6+Community", "Test Empfangsgruppe"],  # "*" bedeutet jede Gruppe
        "trigger_actions": ["JOIN"],  # Aktionen, die den Befehl auslösen
        "function": "sende_Empfangsnachricht"
    },
    {
        "name": "Hilfe für unverständliche Nachrichten",
        "status_condition": lambda status: status >= 2,  # Für Benutzer mit Status >= 2
        "trigger_words": ["unbekannt", "hilfe", "fehler"],
        "trigger_actions": ["WRITE"],  # Aktionen, die den Befehl auslösen
        "function": "send_hilfe"
    },
    {
        "name": "Befehlsausführung",
        "status_condition": lambda status: status >= 2,  # Für Benutzer mit Status >= 2
        "trigger_words": ["start", "stop", "status"],  # Befehle aus einer bestimmten Gruppe
        "trigger_actions": ["WRITE"],  # Aktionen, die den Befehl auslösen
        "function": "do_befehl"
    },
    {
        "name": "Erweiterte Statusmeldung",
        "status_condition": lambda status: status >= 3,  # Für Benutzer mit Status >= 3
        "trigger_words": ["bericht", "fortschritt", "detailliert"],
        "trigger_actions": ["WRITE"],  # Aktionen, die den Befehl auslösen
        "function": "send_status"
    },
    {
        "name": "User Informationen",
        "status_condition": lambda status: status >= 99,  # Für Benutzer mit Status 99 // Ingo ONLY
        "trigger_words": ["Wer", "ist"],
        "function": "send_user_info"
    }
]

 
# ---- MYSQL Datenbank funktionen

# Verbindungsaufbau
def get_db_connection():
    try:
        #print("Verbindung zur Datenbank herstellen...")
        con = pymysql.connect(
            host = os.getenv("host"),  # MySQL-Host
            user = os.getenv("user"),  # Dein MySQL-Benutzername
            password = os.getenv("password"),  # Dein MySQL-Passwort
            database = os.getenv("database"),  # Ziel-Datenbank
            charset="utf8mb4",  # Zeichenkodierung
            cursorclass=pymysql.cursors.DictCursor  # Für dictionary-basierte Ergebnisse
        )
        #print("Verbindung erfolgreich!")
        return con
    except pymysql.MySQLError as err:
        print(f"Fehler: {err}")
        raise
    except Exception as e:
        traceback.print_exc()
        print(f"Fehler: {e}")
        raise

# instertion functions
def insert_group(group_id, **kwarg):
    print(f"Insert group: {group_id}, {kwarg}")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Dynamisch SQL und Werte aus kwarg erzeugen
            columns = ", ".join(kwarg.keys())
            placeholders = ", ".join(["%s" for _ in kwarg.keys()])
            sql = f"INSERT INTO `groups` (group_id, {columns}) VALUES (%s, {placeholders})"
            #print(f"SQL: {sql}")
            values = [group_id] + list(kwarg.values())
            #print(f"Values: {values}")
            cursor.execute(sql, values)
            conn.commit()
            #print(f"Group inserted with ID: {cursor.lastrowid}")
    except Exception as e:
        traceback.print_exc()
        print(f"Fehler beim Einfügen der Gruppe: {e}")
    finally:
        conn.close()

def insert_member(member_id, **kwarg):
    print(f"Insert member: {member_id}, {kwarg}")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Dynamisch SQL und Werte aus kwarg erzeugen
            columns = ", ".join(kwarg.keys())
            placeholders = ", ".join(["%s" for _ in kwarg.keys()])
            sql = f"INSERT INTO members (member_id, {columns}) VALUES (%s, {placeholders})"
            #print(f"SQL: {sql}")
            values = [member_id] + list(kwarg.values())
            #print(f"Values: {values}")
            cursor.execute(sql, values)
            conn.commit()
            #print(f"Member inserted with ID: {cursor.lastrowid}")
    except Exception as e:
        traceback.print_exc()
        print(f"Fehler beim Einfügen des Mitglieds: {e}")    
    finally:
        conn.close()

def insert_group_member(group_id, member_id):
    print(f"Insert group member: {group_id}, {member_id}")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO group_members (group_id, member_id)
                VALUES (%s, %s)
            """
            #print(f"SQL: {sql}")
            try:
                cursor.execute(sql, (group_id, member_id))
                conn.commit()
            except Exception as e:
                traceback.print_exc()
                print(f"Fehler beim Einfügen des Gruppenmitglieds: {e}")
            print("Group-Member relationship inserted.")
    finally:
        conn.close()

def insert_group_admin(group_id, admin_uuid):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO group_admins (group_id, admin_uuid)
                VALUES (%s, %s)
            """
            cursor.execute(sql, (group_id, admin_uuid))
            conn.commit()
            print("Group-Admin relationship inserted.")
    finally:
        conn.close()

# update functions

def update_group_data(group_id, **kwarg):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Dynamisch SQL und Werte aus kwarg erzeugen
            set_clause = ", ".join([f"{key} = %s" for key in kwarg.keys()])
            sql = f"UPDATE `groups` SET {set_clause} WHERE group_id = %s"
            #print(f"SQL: {sql}")
            values = list(kwarg.values()) + [group_id]  # Werte + group_id für WHERE-Bedingung
            
            cursor.execute(sql, values)
            conn.commit()
            #print(f"Group {group_id} updated with {kwarg}.")
    except Exception as e:
        traceback.print_exc()
        print(f"Fehler beim MYQL upload der Gruppe: {e}")
    finally:
        conn.close()

def update_member_status(member_id, **kwarg): 

    conn = get_db_connection() 
    #print(f"Update member: {member_id}, {kwarg}")
    try:
        with conn.cursor() as cursor:
            # Dynamisch SQL und Werte aus kwarg erzeugen
            set_clause = ", ".join([f"{key} = %s" for key in kwarg.keys()])
            sql = f"UPDATE members SET {set_clause} WHERE member_id = %s"
            values = list(kwarg.values()) + [member_id]  # Werte + member_id für WHERE-Bedingung
            
            cursor.execute(sql, values)
            conn.commit()
            #print(f"Member {member_id} updated with {kwarg}.")
    except Exception as e:
        traceback.print_exc()
        print(f"Fehler beim MYQL upload des Mitglieds: {e}")
    finally:
        conn.close()

def update_group_admin(group_id, admin_uuid, revoked=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if revoked is True:
                sql = "UPDATE group_admins SET revoked = %s WHERE group_id = %s AND admin_uuid = %s"
                cursor.execute(sql, (True, group_id, admin_uuid))
            else:
                sql = "UPDATE group_admins SET revoked = %s WHERE group_id = %s AND admin_uuid = %s"
                cursor.execute(sql, (False, group_id, admin_uuid))
            conn.commit()
            print(f"Group-Admin relationship updated.")
    finally:
        conn.close()
# get functions
def get_all_groups():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM `groups`"
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

def get_members_by_group(group_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT m.* 
                FROM members m
                INNER JOIN group_members gm ON m.member_id = gm.member_id
                WHERE gm.group_id = %s
            """
            cursor.execute(sql, (group_id,))
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

def get_group_by_group_id(group_id, get=None):
    """
    Holt die Gruppendaten anhand der group_id.
    """
    conn = get_db_connection()
    #print(f"context: {conn}")
    try:
        with conn.cursor() as cursor:
            # Abfrage dynamisch erstellen
            if get is None:
                sql = f"""
                    SELECT 
                        *
                    FROM 
                        `groups`
                    WHERE 
                        group_id = '{group_id}'
                """
            else:
                columns = ", ".join(get)
                sql = f"SELECT {columns} FROM `groups` WHERE group_id = '{group_id}'"
            
            #print(f"SQL: {sql}")  # Debugging-Ausgabe
            cursor.execute(sql)
            result = cursor.fetchone()
            #print(f"Result: {result}")
            if result is None:
                print("Keine Ergebnisse gefunden.")
            return result
    finally:
        conn.close()

def get_member_by_uuid(uuid, get=None):
    """
    Holt die Benutzerdaten anhand der UUID.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Abfrage dynamisch erstellen
            if get is None:
                sql = f"""
                    SELECT 
                        *
                    FROM 
                        members
                    WHERE 
                        member_id = '{uuid}'
                """
            else:
                columns = ", ".join(get)
                sql = f"SELECT {columns} FROM members WHERE member_id = '{uuid}'"
                print (f"SQL: {sql}")
            
            #print(f"SQL: {sql}")  # Debugging-Ausgabe
            cursor.execute(sql)
            result = cursor.fetchone()
            if result is None:
                print("Keine Ergebnisse gefunden.")
            return result
            
    finally:
        conn.close()

def get_group_members(group_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT * 
                FROM `group_members`
                WHERE group_id = %s
            """
            cursor.execute(sql, (group_id,))
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

def get_group_admins(group_id=None, admin_uuid=None, revoked=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if group_id is not None and admin_uuid is not None:
                sql = """
                    SELECT * 
                    FROM `group_admins`
                    WHERE group_id = %s AND admin_uuid = %s
                """
                sql += " AND revoked != TRUE" if revoked is not True  else ""
                cursor.execute(sql, (group_id, admin_uuid))    
            elif group_id is not None:
                sql = """
                    SELECT * 
                    FROM `group_admins`
                    WHERE group_id = %s
                """
                sql += " AND revoked != TRUE" if revoked is not True  else ""
                cursor.execute(sql, (group_id,))
            elif admin_uuid is not None:
                sql = """
                    SELECT * 
                    FROM `group_admins`
                    WHERE admin_uuid = %s
                """
                sql += " AND revoked != TRUE" if revoked is not True  else ""
                cursor.execute(sql, (admin_uuid,))
            else:
                sql = "SELECT * FROM `group_admins`"
                sql += " WHERE revoked != TRUE" if revoked is not True  else ""
                cursor.execute(sql)
            print(f"SQL: {sql}")
            result = cursor.fetchall()
            return result    
    except Exception as e:  
        traceback.print_exc()
        print(f"Fehler bei der Abfrage der Gruppenadmins: {e}")
    finally:
        conn.close()    
# questions

def is_member_in_group(group_id, member_id):
    #print(f"Check member in group: {group_id}, {member_id}")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT * 
                FROM `group_members`
                WHERE group_id = %s AND member_id = %s
            """
            cursor.execute(sql, (group_id, member_id))
            result = cursor.fetchone()
            return result is not None
    finally:
        conn.close()

def is_member(member_id, retired=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT * 
                FROM `members`
                WHERE member_id = %s
            """
            sql += " AND retired != TRUE" if retired is not True  else ""
            cursor.execute(sql, (member_id,))
            result = cursor.fetchone()
            return result is not None
    except Exception as e:  
        traceback.print_exc()
        print(f"Fehler bei der Abfrage des Mitglieds: {e}")
    finally:
        conn.close()
# --- MYSQL Datenbank funktionen ENDE

# Funktion zum Initialisieren der Logger
class JSONFormatter(logging.Formatter):
    def format(self, record):
        # Prüfen, ob die Nachricht JSON-kompatibel ist
        try:
            parsed_json = json.loads(record.msg)
            # Schöner formatieren (mit Einrückungen)
            record.msg = json.dumps(parsed_json, indent=4, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            # Falls keine JSON-Daten, Nachricht unverändert lassen
            pass
        #print(f"Record: {record}")
        return super().format(record)

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # JSONFormatter für bessere JSON-Darstellung
    formatter = JSONFormatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # FileHandler für Log-Datei
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Wenn Logger noch keine Handler hat, hinzufügen
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger


# Prozesslogik


# --- signal-cli funktionen

def send_by_number(text, phonenumber):
    try:
        # Signal-CLI-Befehl definieren
        cmd = ["sudo", "signal-cli", "-o","json",  "send", phonenumber, "-m", text]

        # Befehl ausführen
        cmd_ausfuehren(cmd)

        return {"code": 0, "text": f"Nachricht an {phonenumber} erfolgreich gesendet"}
    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Senden an {phonenumber}: {e}"}

def send_by_name(text, name):
    try:
        # Signal-CLI-Befehl definieren
        cmd = ["sudo", "signal-cli", "-o","json",  "send", "-u", name, "-m", text]

        # Befehl ausführen
        cmd_ausfuehren(cmd)

        return {"code": 0, "text": f"Nachricht an {name} erfolgreich gesendet"}
    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Senden an {name}: {e}"}

def send_message(message, target_UUID, groupId=None, **kwargs):
    """
        sende nachricht an gruppe
            -g [GROUP_ID [GROUP_ID ...]]
            --mention pos:length:UUID

        sende nachricht an user
            -u [USER [USER ...]]
        
        allgemein:
            - m [MESSAGE]
        
    """
    #print(f"Nachricht: {message} an {target_UUID} in Gruppe {groupId} mit kwargs: {kwargs}")
    try:
        # Signal-CLI-Befehl vorbereiten
        mentions = []
        if kwargs:
            for key, uuid in kwargs.items():
                # Position und Länge des Keys in der Nachricht ermitteln
                pos = message.find(key)
                if pos != -1:  # Nur hinzufügen, wenn der Key im Text gefunden wird
                    len_key = len(key)
                    mentions.append("--mention")
                    mentions.append(f"{pos}:{len_key}:{uuid}")

        # Aufbau des Signal-CLI-Befehls
        if groupId is not None:
            cmd = ["sudo", "signal-cli", "-o", "json", "send", "-g", groupId] + mentions + ["-m", message]

        else:
            cmd = ["sudo", "signal-cli", "-o", "json", "send", "-m", message, target_UUID]

        #print(f"Send Message Command: {cmd}")
        print(f"Nachricht: {message} an {target_UUID} in Gruppe {groupId}")
        # Befehl ausführen
        timestamp = cmd_ausfuehren(cmd)
        return timestamp

    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Senden an {target_UUID}: {e}"}

def get_all_groups(g_id=None):
    try:
        # Signal-CLI-Befehl definieren
        if g_id == None:
            cmd = ["sudo", "signal-cli", "-o", "json", "listGroups", "-d"]
        else:
            cmd = ["sudo", "signal-cli", "-o", "json", "listGroups", "-d", "-g", g_id]
        #print(f"Command: {cmd}")
        # Ausgabe des Kommandos abrufen
        groups = process_linedata(cmd_ausfuehren(cmd))
        #print(f"Gruppen: {json.dumps(groups, indent=4)}")
        group_data = {}  # Dictionary für Gruppendaten
        for group in groups[0]:  # Zugriff auf die Liste mit Gruppen
            group_data[group["name"]] = {
                "id": group["id"],
                "name": group["name"],
                "description": group["description"],
                "memberscount": len(group["members"]),
                "banned": group["banned"],
                "permissionAddMember": group["permissionAddMember"],
                "permissionEditDetails": group["permissionEditDetails"],
                "permissionSendMessage": group["permissionSendMessage"],
                "groupInviteLink": group["groupInviteLink"],
                "admins": group["admins"]

            }
            group_data[group["name"]]["admins"] = []
            for admin in group["admins"]:
                group_data[group["name"]]["admins"].append(admin["uuid"])
            

        #print (f"Gruppen: {json.dumps(group_data, indent=4)}")
                
        return group_data
        
    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Abrufen der Gruppen: {e}"}

def get_all_messages():
    try:
        # Signal-CLI-Befehl definieren
        cmd = ["sudo", "signal-cli", "-o","json",  "receive", "--send-read-receipts"]

        # Ausgabe des Kommandos abrufen
        
        communication_logger.info(f"Starte Nachrichtenabfrage")
        messages = cmd_ausfuehren(cmd)
        communication_logger.info(f"Nachrichtengeholt: {messages}") if messages != "" else None
        return messages
    except Exception as e:
        traceback.print_exc()
        return [{"code": -1, "text": f"Fehler: {e}"}] 

def get_message():
    try:
        # Signal-CLI-Befehl definieren
        cmd = ["sudo", "signal-cli", "-o","json",  "receive", "--send-read-receipts", "--max-messages", "1" ]

        # Ausgabe des Kommandos abrufen
        communication_logger.info(f"Starte Nachrichtenabfrage")
        message = cmd_ausfuehren(cmd)
        communication_logger.info(f"Nachrichtengeholt: {message}")
        return message

    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler: {e}"}

def get_signal_user(uuid=None):
    try:
        # Signal-CLI-Befehl definieren
        if uuid == None:
            cmd = ["sudo", "signal-cli", "-o", "json", "listContacts", "--detailed", "-a" ]
        else:
            cmd = ["sudo", "signal-cli", "-o", "json", "listContacts", "--detailed", "-a", uuid]
        
        # Ausgabe des Kommandos abrufen
        contacts = process_linedata(cmd_ausfuehren(cmd))
        return contacts
    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Abrufen der Kontakte: {e}"}

def send_typing(uuid, action):
    try:
        # Signal-CLI-Befehl definieren
        cmd = ["sudo", "signal-cli", "-o", "json", "sendTyping", uuid, action]

        # Ausgabe des Kommandos abrufen
        cmd_ausfuehren(cmd)
    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Senden des Schreibstatus: {e}"}
# --- signal-cli funktionen ENDE

# --- Funktionen für die Verarbeitung von Nachrichten

def cmd_ausfuehren(cmd):
    try:
        # Führe den Befehl aus und fange die Ausgabe ein
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        #print(f"Alles: {result}")
        # Überprüfen, ob der Befehl erfolgreich war
        if result.returncode != 0:
            raise debug_logger.info(f"Fehler beim Ausführen des Befehls: {result.stderr}")

        if result.stdout == "":
            return ""

        return result.stdout
    
    except Exception as e:
        traceback.print_exc()
        raise debug_logger.info(f"Fehler in cmd_ausfuehren beim Ausführen des Kommandos: {e}")

def process_linedata(data):
    messages =[] 

    for line in data.splitlines():
        communication_logger.info(f"Nachricht: {line}")

        parsed_data = json.loads(line)
        messages.append(parsed_data)
        
    return messages

def do_group_update(group_id):
    try:
        g_data = get_all_groups(group_id)
        print(f"Gruppeninfo: {json.dumps(g_data)}")
        if g_data is not None:
            for group in g_data:
                #print(f"Gruppe: {json.dumps(group)}")
                update_group_data(
                    group_id, 
                    members_count=g_data[group]["memberscount"],
                    description=g_data[group]["description"], 
                    permission_add_member=g_data[group]["permissionAddMember"], 
                    permission_edit_details=g_data[group]["permissionEditDetails"], 
                    permission_send_message=g_data[group]["permissionSendMessage"], 
                    group_invite_link=g_data[group]["groupInviteLink"]
                )
                print(f"Gruppe {group_id} aktualisiert")

                admins = get_group_admins(group_id, None, True)
                print (f"Admins: {json.dumps(admins)}")
                for admin in g_data[group]["admins"]:
                    if admin not in admins:
                        insert_group_admin(group_id, admin)
                        print(f"Admin {admin} hinzugefügt")




        else:
            print(f"Keine Daten für Gruppe {group_id} verfügbar")
    except Exception as e:
        traceback.print_exc()
        print(f"Fehler bei der Aktualisierung der Gruppe {group_id}: {e}")


    

def process_command(messages):
    #print("Starte Verarbeitung der Nachrichten")

    """ Die funktion prüft 
    - ob die Nachricht eine Uuid enthält 
    -> ob die Uuid in der Datenbank vorhanden ist
    --> update der daten sourceName--> Name, now()-> "Last seen"  in der Datenbank
    - ob die Nachricht ein Kommando aus der liste enthält
    -> ausführung des Kommandos
    -> Speichern der Antwort_timestamp in der Datenbank db. table("sendmessages")
    und ob die """

    for message in messages:
        print("\n\n\nNeue Nachricht erhalten\n")
        if "envelope" in message:
            
            uuid = message["envelope"]["sourceUuid"]
            name = message["envelope"]["sourceName"]
            if "receiptMessage" in message["envelope"]:
                if message["envelope"]["receiptMessage"]["isDelivery"]:
                    print("Zustellbestätigung erhalten")
                elif message["envelope"]["receiptMessage"]["isRead"]:
                     print("Lesebestätigung erhalten")
                else:
                    print("Unbekannte Bestätigung erhalten")
                user = get_member_by_uuid(uuid)
                if user != None:
                    if user["name"] == None and name!= None:
                        update_member_status(uuid, name=name)

                    if message["envelope"]["receiptMessage"]["isDelivery"]:
                        update_member_status(uuid, last_delivered=datetime.now() )
                    if message["envelope"]["receiptMessage"]["isRead"]:
                        update_member_status(uuid, last_read=datetime.now() )
            
            elif "dataMessage" in message["envelope"]:
                body = message["envelope"]["dataMessage"]["message"]
                if "groupInfo" in message["envelope"]["dataMessage"]:
                    groudInfo = message["envelope"]["dataMessage"]["groupInfo"]
                    groupid = message["envelope"]["dataMessage"]["groupInfo"]["groupId"] if groudInfo != None else None
                    groupname = message["envelope"]["dataMessage"]["groupInfo"]["groupName"] if groudInfo != None else None
                if body != None:
                    #Textnachricht
                    print(f"Nachricht: {body}")
               
                    # User-Level aus der Datenbank abrufen
                    user = get_member_by_uuid(uuid, ["level"])
                    print(f"User: {user}")
                    print(f"User-Level: {user['level']}")
                    if user != None:
                        update_member_status(uuid, active=datetime.now() )

                    
                    for modus in modis:
                        if modus["status_condition"](user['level']):  # Prüfen, ob der Status passt
                            print(f"Modus: {modus['name']}")
                            if any(trigger in body for trigger in modus["trigger_words"]) or "*" in modus["trigger_words"]:
                                print(f"Nachricht: {body}")
                                globals()[modus["function"]](uuid)  # Funktion ausführen
                else:
                    #sonstige nachrichten
                    if groudInfo != None:
                        try:
                            #irgendwas mit gruppen
                            typ = message['envelope']['dataMessage']['groupInfo']['type']
                            print(f"Gruppeninfo: {typ}")
                            if typ == "UPDATE":
                                do_group_update(groupid)
                        except Exception as e:
                            traceback.print_exc()
                            print(f"Fehler bei der Verarbeitung der Gruppeninfo: {e}")
            elif "typingMessage" in message["envelope"]:
                    print(f"{name} schreibt...") if message["envelope"]["typingMessage"]["action"] == "START" else print(f"{name} hat aufgehört zu schreiben")
            else:
                print("keine bekannte Nachricht")
                print(f"Nachricht: {json.dumps(message, indent=4)}")
        else:
            print("kein Envelope in der Nachricht")


# --- Funktionen für die Verarbeitung von Nachrichten ENDE

# --- Funktionen für die Befehlsausführung
def send_wegweiser(uuid):
    wegweiser_txt = (
    "Hallo! 😊\n"
    "Ich bin der Service-Bot der sexpositiven Community.\n\n"
    "Um Teil der Community zu werden, musst du zuerst am Eingang vorbeischauen. "
    "Keine Sorge, das ist ganz einfach! Der Eingang befindet sich hier:\n\n"
    "https://signal.group/#CjQKIK_jXWsAHQL0yPJoKvcqje4PR4ygeZ-PLUyFJWMTk3EZEhCRKZ1HLOmBEE21dbk1J1AP\n\n"
    "Wir freuen uns darauf, dich willkommen zu heißen! ❤️"
    )

    send_message(wegweiser_txt, uuid)
 
# --- Funktionen für die Befehlsausführung ENDE

# --- Funktionen für synchronisierung und aktualisierung der Datenbank
def update_db_on_startup():
    try:
        # Signal-CLI-Befehl definieren
        cmd = ["sudo", "signal-cli", "-o", "json", "listGroups"]
        
        # Ausgabe des Kommandos abrufen
        groups = process_linedata(cmd_ausfuehren(cmd))
        #print(f"Gruppen: {json.dumps(groups[0], indent=4)}")
        #pause = input("Gruppen abgerufen. Enter zum fortfahren...")
        for group in groups[0]:  # Zugriff auf die Liste mit Gruppen
            group_data= get_group_by_group_id(group["id"], ["id"])
            
            if group_data == None:
                insert_group(group["id"],
                            group_name=group["name"],
                            description=group["description"],
                            permission_add_member=group["permissionAddMember"],
                            permission_edit_details=group["permissionEditDetails"],
                            permission_send_message=group["permissionSendMessage"],
                            group_invite_link=group["groupInviteLink"])
                group= get_group_by_group_id(group["id"])
                print(f"Neue Gruppe: {group['name']} mit ID: {group['id']}")
            else:
                print(f"Gruppe: {group['name']}")
            membercount =0
            for member in group["members"]:
                try:
                    #Mitglieder abfragen
                    member_data = get_member_by_uuid(member["uuid"])
                    membercount += 1

                    
                    # Mitglied einfuegen, wenn nicht vorhanden
                    if is_member(member["uuid"]) == False:
                        signal_data=get_signal_user(member["uuid"])
                        if signal_data != None:
                            print(f"Signal User: {json.dumps(signal_data[0], indent=4)}")
                            insert_member(
                                member["uuid"],
                                name=signal_data[0]["username"],
                                givenname=signal_data[0]["profile"]["givenName"],
                                familyname=signal_data[0]["profile"]["familyName"],
                                phone=signal_data[0]["phoneNumber"],
                                level=0,
                                )
                            get_group_members(group["id"])
                            print(f"Neues Member: {member['uuid']}")
                        else:
                            print(f"Signal User nicht gefunden: {member['uuid']}")
                    
                        
                    
                    # Mitglied der Gruppe hinzufügen, wenn nicht vorhanden
                    if  is_member_in_group(group["id"], member["uuid"]) == False:
                        insert_group_member(group["id"], member["uuid"])
                        send_message("Hallo name, willkommen in der Gruppe", member["uuid"], group["id"], name=member["uuid"])
                    
                except Exception as e:
                    traceback.print_exc()
                    print(f"Fehler beim Einfügen des Mitglieds: {e}")
                    continue
            
            print(f"Mitgliederanzahl: {membercount}")

        
    except Exception as e:
        traceback.print_exc()
        return {"code": -1, "text": f"Fehler beim Abrufen der Gruppen: {e}"}

# Funktion, die prüft, ob das Skript aktualisiert wurde
def check_for_updates(start_time):
    # Pfad zur aktuellen Skriptdatei
    script_path = os.path.abspath(__file__)
    # Änderungszeit der Datei abrufen
    last_modified_time = os.path.getmtime(script_path)
    # Prüfen, ob die Datei seit dem Start geändert wurde
    return last_modified_time > start_time

# Funktion zum Initialisieren des Loggers
debug_logger = setup_logger('SPC_bot_debug', 'SPC_bot_debug.log')
communication_logger = setup_logger('SPC_bot_communication', 'SPC_bot_communication.log')

debug_logger.info(f"Starte Skript...")
communication_logger.info(f"Starte Skript...")   

# ----------- Datenbank initialisieren -----------
print("Initialisiere Datenbank...")

update_db_on_startup()


print("Fertig!\n\n")
#pause = input("Datenbank erstellt. Enter zum fortfahren...")



# ----------- Hauptprogramm -----------

# Startzeit des Skripts speichern
start_time = time.time()


update_interval = 15
print_increments = 5
countdown_time =0
printout = True

while True:
    print("Sleeping ZZZZ                                         ", end="\r")  # Löscht die Zeile
    while countdown_time >= 0:
        
        #print(f"Start in: {countdown_time} Sekunden verbleiben ", end="\r")  # Überschreibt die Zeile
        time.sleep(print_increments)  # 5 Sekunden warten
        countdown_time -= print_increments
        
    print("Working                                               ", end="\r")  # Löscht die Zeile

    if check_for_updates(start_time):
        print("Neue Version des Skripts erkannt. Starte neu...")
        # Skript neu starten
        subprocess.Popen([sys.executable, os.path.abspath(__file__)])
        sys.exit()  # Beendet das aktuelle Skript


    #programmablauf
    debug_logger.info("Starte Nachrichtenabfrage")
    #print("---Starte Nachrichtenabfrage\n") if printout else None
    data = get_all_messages()
    #print(f"Eingehende Nachricht(en): {data}") if printout else None
    if data != "" and data != None:
        processed_data = process_linedata(data)
        #print(f"Verarbeitete Nachricht(en):\n {json.dumps(processed_data, indent=4)}") if printout else None
        process_command(processed_data)
    
    #print ("---Ende Nachrichtenabfrage \n\n") if printout else None

    #end programmablauf

    countdown_time = update_interval


    

#


"""# Beispielaufruf für alle Nachrichten
print("Starte Nachrichtenabfrage")
data = get_all_messages()
print(data)
print ("Ende Nachrichtenabfrage \n")

print("Starte Gruppemabfrage")
# Beispielaufruf für alle Gruppen
get_all_groups()
"""



