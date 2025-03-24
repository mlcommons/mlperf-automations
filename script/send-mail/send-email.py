import smtplib
import sys
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email import encoders


def send_email(subject, to_addresses, cc_addresses, bcc_addresses, content_file,
               attachments, use_smtp_server=False, smtp_server=None, email=None, password=None):

    to_list = to_addresses.split(',')
    cc_list = cc_addresses.split(',')
    bcc_list = bcc_addresses.split(',')
    attachment_list = attachments.split(',')

    with open(content_file, 'r') as file:
        email_content = file.read()

    msg = MIMEMultipart()
    msg['From'] = email if use_smtp_server else 'localhost'
    msg['To'] = COMMASPACE.join(to_list)
    msg['Cc'] = COMMASPACE.join(cc_list)
    msg['Subject'] = subject

    msg.attach(MIMEText(email_content, 'plain'))

    for attachment in attachment_list:
        with open(attachment, 'rb') as file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={attachment}')
            msg.attach(part)

    recipients = to_list + cc_list + bcc_list

    if use_smtp_server:
        with smtplib.SMTP_SSL(smtp_server) as server:
            server.login(email, password)
            server.sendmail(email, recipients, msg.as_string())
            print("Email sent successfully using SMTP server!")
    else:
        with smtplib.SMTP('localhost') as server:
            server.sendmail(
                'localhost@example.com',
                recipients,
                msg.as_string())
            print("Email sent successfully using localhost!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Send an email with specified attachments')
    parser.add_argument('subject', type=str, help='Email subject')
    parser.add_argument(
        'to_addresses',
        type=str,
        help='To addresses, comma-separated')
    parser.add_argument(
        'cc_addresses',
        type=str,
        help='CC addresses, comma-separated')
    parser.add_argument(
        'bcc_addresses',
        type=str,
        help='BCC addresses, comma-separated')
    parser.add_argument(
        'content_file',
        type=str,
        help='File containing email content')
    parser.add_argument(
        'attachments',
        type=str,
        help='Attachments, comma-separated file paths')

    parser.add_argument(
        '--use_smtp_server',
        action='store_true',
        help='Use an SMTP server instead of localhost')
    parser.add_argument(
        '--email',
        type=str,
        help='Email address for SMTP server')
    parser.add_argument(
        '--password',
        type=str,
        help='Password for SMTP server')
    parser.add_argument('--smtp_server', type=str, help='SMTP server address')

    args = parser.parse_args()

    if args.use_smtp_server and not all(
            [args.email, args.password, args.smtp_server]):
        parser.error(
            '--email, --password, and --smtp_server are required when --use_smtp_server is set')

    send_email(
        args.subject,
        args.to_addresses,
        args.cc_addresses,
        args.bcc_addresses,
        args.content_file,
        args.attachments,
        args.use_smtp_server,
        args.smtp_server,
        args.email,
        args.password)
