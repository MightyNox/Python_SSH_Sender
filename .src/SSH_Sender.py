import paramiko
import json
import os
import socket
import datetime


def connect(server_address, port, user, password):
    print("User: {0}".format(user))
    print("Connecting: {0}".format(server_address))
    print("Port: {0}".format(port))

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_address, port, user, password)
        print("Connected")
        print()
        return ssh
    except paramiko.ssh_exception.AuthenticationException:
        exit("Wrong password!")
    except paramiko.ssh_exception.NoValidConnectionsError:
        exit("No valid connection!")
    except socket.gaierror:
        exit("Invalid address!")
    except Exception:
        exit("Error occurred (wrong port)!")


# Load config from config.json
def load_config():
    try:
        with open("config.json") as json_data:
            data = json.load(json_data)
    except json.decoder.JSONDecodeError:
        exit("JSON Error!")
    return data["server_address"], data["port"], data["username"], \
           input("password: "), data["local_folder"], \
           data["remote_folder"], data["mode"], data["ignore"]


# Overwrite all files
def overwrite(local_folder, sftp, ssh, ignore):
    for root, dirs, files in os.walk(local_folder):
        for filename in files:
            try:
                if ignore_extension(filename, ignore):
                    try:
                        sftp.put(local_folder + filename, filename)
                        print(filename)
                    except FileNotFoundError:
                        ssh.close()
                        exit("Wrong local folder!")
            except IndexError:
                ssh.close()
                exit("Local folder is empty!")
    ssh.close()


# Update only older files
def update(local_folder, sftp, ssh, ignore):
    for root, dirs, files in os.walk(local_folder):
        for filename in files:
            try:
                if ignore_extension(filename, ignore):
                    try:
                        sftp.stat(filename)
                        date1 = datetime.fromtimestamp(os.path.getmtime(local_folder + filename))
                        date2 = datetime.fromtimestamp(sftp.stat(filename).st_mtime)

                        if date1 > date2:
                            sftp.put(local_folder + filename, filename)
                            print(filename)

                    except FileNotFoundError:
                        ssh.close()
                        exit("Wrong local folder!")
                    except IOError:
                        pass
            except IndexError:
                ssh.close()
                exit("Local folder is empty!")
    ssh.close()


# Add non existing files
def add_non_existing(local_folder, sftp, ssh, ignore):
    for root, dirs, files in os.walk(local_folder):
        for filename in files:
            try:
                if ignore_extension(filename, ignore):
                    try:
                        sftp.stat(filename)
                    except IOError:
                        try:
                            sftp.put(local_folder + filename, filename)
                            print(filename)
                        except FileNotFoundError:
                            ssh.close()
                            exit("Wrong local folder!")
            except IndexError:
                ssh.close()
                exit("Local folder is empty!")
    ssh.close()


# Ignored extensions
def ignore_extension(filename, ignore):
    x = filename.split(".")
    flag = True
    for y in ignore:
        if x[1] == y:
            flag = False
            break
    if flag:
        return True
    return False


# Check if local folder exists
def check_local_folder(local_folder):
    if not os.path.isdir(local_folder):
        exit("Wrong local folder!")


def main():
    host, port, user, password, local_folder, remote_folder, mode, ignore = load_config()
    check_local_folder(local_folder)

    ssh = connect(host, port, user, password)
    sftp = ssh.open_sftp()
    try:
        sftp.chdir(remote_folder)
    except FileNotFoundError:
        ssh.close()
        exit("Wrong remote folder!")

    # Select overwrite|update|add_non_existing
    try:
        print("Selected mode: {0}".format(mode))
        if mode == "overwrite":
            overwrite(local_folder, sftp, ssh, ignore)
        elif mode == "update":
            update(local_folder, sftp, ssh, ignore)
        elif mode == "add_non_existing":
            add_non_existing(local_folder, sftp, ssh, ignore)
        else:
            ssh.close()
            exit("Wrong mode!")
    except PermissionError:
        exit("Permission denied!")


if __name__ == "__main__":
    main()
    print("Transfer successful")
