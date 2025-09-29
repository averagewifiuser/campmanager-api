import requests
from globals import SMTP2GO_API_KEY

from flask import render_template


class Mailer(object):
    def __init__(self):
        self.api_key = SMTP2GO_API_KEY
        self.api_url = "https://api.smtp2go.com/v3/email/send"

    def generate_email_text(self, template_name, context={}):
        return render_template(template_name, **context)

    def send_email(
        self,
        recipients,
        subject,
        text,
        sender="CampManager Support <support@wedidtech.com>",
        html=False,
        attachments=None,
    ):
        """
        Sends an email using the SMTP2GO API.

        :param sender: Email address of the sender
        :param recipient: Email address of the recipient
        :param subject: Subject of the email
        :param body: Body of the email (plain text or HTML)
        :param html: Boolean indicating if the body is HTML
        :return: Response from the SMTP2GO API
        """

        headers = {"accept": "application/json", "Content-Type": "application/json"}
        payload = {
            "api_key": self.api_key,
            "to": recipients,
            "sender": sender if sender else "CampManager Support <support@wedidtech.com>",
            "subject": subject,
            "text_body": text if not html else None,
            "html_body": text if html else None,
        }
        if attachments:
            # SMTP2GO expects base64 content under 'fileblob'
            payload["attachments"] = [
                {
                    "filename": att.get("filename"),
                    "fileblob": att.get("fileblob"),
                    "mimetype": att.get("mimetype", "application/octet-stream"),
                    "content_id": att.get("filename"),
                }
                for att in attachments
                if att and att.get("filename") and att.get("fileblob")
            ]
        
        print(payload)  # Debug print to check payload structure
        response = requests.post(self.api_url, headers=headers, json=payload)
        print(response.json())
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()


mailer = Mailer()
