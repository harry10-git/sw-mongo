# import email modules
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List
from config import settings

def send_email(From: str,
               To: str | List[str],
               Subject: str,
               Body: str,
               CC: str | List[str] | None = None,
               BCC: str | List[str]| None = None,
               Attachment=None, AttachmentName=None, AttachmentType='application/octet-stream', SMTPServer=None, SMTPPort=None, SMTPUser=None, SMTPPassword=None):
    """Send email using Gmail SMTP server"""

    # set variables
    if SMTPServer is None:
        SMTPServer = settings.SMTP_SERVER
    if SMTPPort is None:
        SMTPPort = settings.SMTP_PORT
    if SMTPUser is None:
        SMTPUser = settings.SMTP_USER
    if SMTPPassword is None:
        SMTPPassword = settings.SMTP_PASSWORD

    # create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Subject
    msg['From'] = From

    # define To if specified as list or string
    msg['To'] = ', '.join(To) if isinstance(To, list) else To
    all_recipients: List[str] = To if isinstance(To, list) else [To]

    # define CC and BCC if specified as list or string
    if CC is not None:
        msg['CC'] = ', '.join(CC) if isinstance(CC, list) else CC
        all_recipients = all_recipients + \
            CC if isinstance(CC, list) else all_recipients + [CC]
    if BCC is not None:
        # msg['BCC'] = ', '.join(BCC) if isinstance(BCC, list) else BCC not needed
        all_recipients = all_recipients + \
            BCC if isinstance(BCC, list) else all_recipients + [BCC]

    # create the body of the message (a plain-text and an HTML version).
    text = Body
    html = Body

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # add attachment if specified
    if Attachment is not None:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(Attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        "attachment; filename= %s" % AttachmentName)
        msg.attach(part)

    # send email
    server = smtplib.SMTP(SMTPServer, SMTPPort)
    server.starttls()
    server.login(SMTPUser, SMTPPassword)
    text = msg.as_string()
    server.sendmail(From, all_recipients, text)
    server.quit()

    return True