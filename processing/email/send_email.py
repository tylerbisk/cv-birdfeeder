import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import ssl
import datetime


def send_email(send_from,
              send_to,
              password,
              text,
              link,
              attach,
              timestamp,
              file=None):

    to_mail_list = ", ".join(send_to)
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = to_mail_list
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = text

    # msg.attach(MIMEText(text))

    date_time = timestamp.strftime("%-I:%M:%S %p on %B %d, %Y")

    if link is not None:
        html = """\
        <html>
          <body>
            <p>
              {} at {}
              <a href="{}">Click here to view more</a> 
            </p>
          </body>
        </html>
        """.format(text, date_time, link)
    else:
        html = """\
        <html>
          <body>
            <p>
               {} at {}
            </p>
          </body>
        </html>
        """.format(text, date_time)

    html_ = MIMEText(html, "html")

    if file is not None and attach:
        file_ = MIMEApplication(open(file, "rb").read(), Name=basename(file))
        file_['Content-Disposition'] = 'attachment; filename="%s"' % basename(
            file)
        msg.attach(file_)

    msg.attach(html_)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(send_from, password)
        server.sendmail(send_from, send_to, msg.as_string())