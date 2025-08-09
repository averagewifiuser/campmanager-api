import requests
from globals import SMS_API_KEY

class SMS(object):
    def __init__(self):
        self.api_key= SMS_API_KEY
        self.sender_id= 'NBC2025'


    def send_sms(self, phone_number, message):
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        base_url = "https://sms.arkesel.com/api/v2/sms/send"

        # SEND SMS
        sms_payload = {
            "sender": self.sender_id,
            "message": message,
            "recipients": [phone_number]
        }

        try:
            response = requests.post(base_url, headers=headers, json=sms_payload)
            response.raise_for_status()
            print(response.text)
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)
        return response.json()



sms= SMS()
