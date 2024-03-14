import requests
import json
from tkinter import filedialog
import tkinter as tk
import re
import chardet
import time
import os
from colorama import Fore, Style

def save_progress(counter):
    with open("progress.txt", "w") as file:
        file.write(str(counter))

def load_progress():
    if os.path.exists("progress.txt"):
        with open("progress.txt", "r") as file:
            return int(file.read())
    else:
        return 1
    
def extract_user_ids_from_file(file_path):
    with open(file_path, 'rb') as file:
        detector = chardet.universaldetector.UniversalDetector()
        for line in file:
            detector.feed(line)
            if detector.done:
                break
        detector.close()
        encoding = detector.result['encoding']

    with open(file_path, 'r', encoding=encoding) as file:
        user_id_list = []
        for line in file:
            # Use regular expression to extract user IDs
            user_ids = re.findall(r'usr_[a-f0-9-]+', line)
            user_id_list.extend(user_ids)
    
    return user_id_list

def select_user_id_from_file():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Select the file containing the list of users")

    if not file_path:
        print("File selection canceled.")
        return None

    user_id_list = extract_user_ids_from_file(file_path)
    return user_id_list

def send_invite_to_group(group_id: str, user_id: str, auth_cookie: str, user_counter: int, total_users: int):
    url = f"https://api.vrchat.cloud/api/1/groups/{group_id}/invites"
    
    headers = {
        "User-Agent": "VRCST/1.0 (your_contact_info)",
        "Cookie": f"auth={auth_cookie}",
        "Content-Type": "application/json"
    }

    data = {
        "userId": user_id
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        message = f"{Fore.GREEN}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : Invitation successfully sent to user {user_id} to join group {group_id}."
        print(message)
        time.sleep(300)  # Pause for 5 minutes before the next iteration
    elif response.status_code == 403:
        error_message = response.json().get('error', {}).get('message', '')
        message = f"{Fore.RED}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : Request failed with status code 403. Server error message: {error_message}. Skipping invitation for user {user_id}."
        print(message)
    elif response.status_code == 400:
        try:
            error_message = response.json().get('error', {}).get('message', '')
            if "is already invited" in error_message:
                message = f"{Fore.YELLOW}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : {user_id} is already invited to this group. Skipping."
            elif "is already a member of this group" in error_message:
                message = f"{Fore.YELLOW}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : {user_id} is already a member of this group. Skipping."
            else:
                message = f"{Fore.RED}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : Request failed with status code {response.status_code}. Server error message: {error_message}."
            print(message)
        except json.JSONDecodeError:
            print("Unable to decode server error message.")
    elif response.status_code == 429:
        message = f"{Fore.RED}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : Request failed with status code 429 (Rate Limit Exceeded). Waiting for 5 minutes before retrying..."
        print(message)
        time.sleep(300)  # Pause for 5 minutes before retrying
        send_invite_to_group(group_id, user_id, auth_cookie, user_counter, total_users)  # Retry after waiting
    else:
        message = f"{Fore.RED}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : Request failed with status code {response.status_code}."
        try:
            error_message = response.json().get('error', {}).get('message', '')
            message += f" Server error message: {error_message}."
        except json.JSONDecodeError:
            print("Unable to decode server error message.")
        print(message)

def get_group_members(group_id: str, auth_cookie: str):
    url = f"https://api.vrchat.cloud/api/1/groups/{group_id}/members"

    headers = {
        "User-Agent": "VRCST/1.0 (your_contact_info)",
        "Cookie": f"auth={auth_cookie}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        group_members = response.json()
        return [member.get("id", "") for member in group_members]
    else:
        print(f"Request to get group members failed with status code {response.status_code}")
        return []

# Ask the user to enter credentials
print(Fore.YELLOW + "Enter your auth_cookie and group_id:")
auth_cookie = input(Style.RESET_ALL + "Enter auth_cookie: ")
group_id = input("Enter group ID: ")

# Select users to invite from a file
user_id_list = select_user_id_from_file()

if user_id_list:
    total_users = len(user_id_list)

    # Get current group members
    group_members = get_group_members(group_id, auth_cookie)

    # Load progress counter
    start_counter = load_progress()

    # Loop over the list of users to invite
    for i, user_id in enumerate(user_id_list[start_counter - 1:], start=start_counter):
        user_counter = i
        if user_id in group_members:
            message = f"{Fore.YELLOW}INFO{Style.RESET_ALL} - User {user_counter}/{total_users} - ID: {user_id} : Message : The user {user_id} is already a member of group {group_id}."
            print(message)
        else:
            send_invite_to_group(group_id, user_id, auth_cookie, user_counter, total_users)
        
        # Save progress after each iteration
        save_progress(user_counter)
