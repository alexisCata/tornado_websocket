import requests
import json

if __name__ == "__main__":

    header = {
        "Content-Type": "application/json",
        "Authorization": "key=AIzaSyB0_60LfwfxIqWvx34d_-Tqd7TPFhMcwJ4",
    }

    body = json.dumps({"to": "eM5so0lASZc:APA91bG8Lsg6lJfylbBYxMvmEFI2foXPfS27B1YXCzmo8tLILY6NP7uxIygY9Hb6KRrEnri-P542b3eTbBW9dkl7qIXUBWtRcC1yBLbHVksVMW-B0SOSKDqjhIyHnPKM5V8Sh7tRbcV8",
            "notification": {"title": "MYNOTIFICATION",
                             "body": "my text notification"}})
    r = requests.post("https://fcm.googleapis.com/fcm/send", data=body, headers=header)

    a = 1;
