#coding:utf8

'''
    这个模块包含设置告警的代码
'''
import sys
import logging
import smtplib
import string

from flask import request
from logging.handlers import SMTPHandler, RotatingFileHandler

reload(sys) 
sys.setdefaultencoding('utf8')


def get_ip_address(ifname='eth1'):
    try:
        import socket
        import fcntl
        import struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915, # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])
    except:
        return ''

ip = get_ip_address()
try:
    import socket
    server = socket.gethostname()
except:
    server = "unkown"


class SSLSMTPHandler(SMTPHandler):
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            from email.utils import formatdate
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=self._timeout)
            real_ip = request.headers.get("X-Real-Ip", "")
            ref = request.headers.get("Referer", "")
            header = "X-Real-Ip:%s\r\nReferer:%s\r\n" % (real_ip, ref)
            msg = header + "%s\r\n%s\r\n%s\r\n" % (ip, request.url, request.values.to_dict()) + self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            "%s (%s)" % (self.getSubject(record) , server),
                            formatdate(), msg)
            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

def enable_logging(app):
    config = app.config['LOGGING']
    config_mail = config.get('SMTP')
    if config_mail: #如果存在smtp配置
        app.logger.info('Add SMTP Logging Handler')
        mail_handler = SSLSMTPHandler(
            (config_mail['HOST'], 465),  #smtp 服务器地址
            config_mail['USER'], #smtp 发件人
            config_mail['TOADDRS'], #smtp 收件人
            config_mail['SUBJECT'], #smtp 主题
            (config_mail['USER'],config_mail['PASSWORD'])) #smtp账号密码
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    else:
        app.logger.info('No SMTP Config Found')

    config_file = config.get('FILE')
    if config_file: #如果存在文件配置
        app.logger.info( 'Add File Logging Handler' )
        file_handler = RotatingFileHandler(
            config_file['PATH'], #文件路径
            #但个文件大小 默认10M 
            maxBytes  = config_file.setdefault('MAX_BYTES',1024 * 1024 * 10), 
            #文件备份>数量 默认5个
            backupCount = config_file.setdefault('BACKUP_COUNT',5), 
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    else:
        app.logger.info('No FILE Config Found')
