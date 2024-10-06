import json
from instagrapi import Client
from concurrent.futures import ThreadPoolExecutor
import os
import logging

config_file = 'config.json'
session_file = 'session.json'

logging.basicConfig(filename='insta_messages.log', level=logging.INFO)

def load_credentials():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def save_credentials(username, password):
    with open(config_file, 'w') as f:
        json.dump({'username': username, 'password': password}, f)

def save_session(client):
    with open(session_file, 'w') as f:
        json.dump(client.get_settings(), f)

credentials = load_credentials()

if credentials:
    username = credentials['username']
    password = credentials['password']
    print("Loaded credentials from config file.")
else:
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    save_credentials(username, password)

cl = Client()

if os.path.exists(session_file):
    cl.load_settings(session_file)
else:
    try:
        cl.login(username, password)
        print("Logged in successfully!")
        save_session(cl)
    except Exception as e:
        if "Two-factor authentication required" in str(e):
            verification_code = input("Enter the 2FA verification code: ")
            cl.login(username, password, verification_code=verification_code)
            print("Logged in successfully with 2FA!")
            save_session(cl)
        else:
            print(f"Failed to log in: {e}")
            exit()

while True:
    threads = cl.direct_threads()
    usernames = set()

    for thread in threads:
        for user in thread.users:
            usernames.add(user.username)

    if usernames:
        print("Usernames in your direct messages:")
        for idx, user in enumerate(usernames):
            print(f"{idx + 1}. {user}")

    recipient_choice = input("Enter the recipient's username or select from the list (number): ")

    # Check if the input is a digit and within range
    if recipient_choice.isdigit():
        try:
            recipient_username = list(usernames)[int(recipient_choice) - 1]
            recipient_id = cl.user_id_from_username(recipient_username)
        except IndexError:
            print("Invalid choice. Please try again.")
            continue
    else:
        try:
            recipient_id = cl.user_id_from_username(recipient_choice)
            recipient_username = recipient_choice  # Set username for logging
        except Exception as e:
            print(f"Failed to find user: {e}. Please ensure the username is correct.")
            continue

    while True:
        message = input("Enter the message to send: ")
        message_count = 23

        with ThreadPoolExecutor(max_workers=10) as executor:
            for _ in range(message_count):
                try:
                    print(f"Sending message: '{message}' to {recipient_username}")
                    executor.submit(cl.direct_send, message, [recipient_id])
                except Exception as e:
                    print(f"Failed to send message: {e}")

        logging.info(f"{message_count} messages sent to {recipient_username}: {message}")
        print(f"{message_count} messages sent to {recipient_username}.")

        send_again = input("Do you want to send the same message again to the same user? (yes/no): ").strip().lower()
        if send_again != 'yes':
            break

    change_recipient = input("Do you want to send messages to a different user? (yes/no): ").strip().lower()
    if change_recipient != 'yes':
        print("Exiting the script.")
        break

print("All messages have been sent.")
