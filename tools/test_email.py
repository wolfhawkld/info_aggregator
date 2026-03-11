#!/usr/bin/env python3
"""
邮箱连通性测试工具
测试SMTP配置是否正确，发送测试邮件
"""

import os
import sys
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def load_config(config_file: str = 'config/config.yaml') -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_smtp_connection(email_config: dict) -> tuple:
    """
    测试SMTP连接

    Returns:
        (success: bool, message: str)
    """
    server = None
    try:
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 465)
        sender = email_config.get('sender')
        password = email_config.get('password')
        use_tls = email_config.get('use_tls', True)

        print(f"SMTP服务器: {smtp_server}:{smtp_port}")
        print(f"发件人: {sender}")
        print(f"密码长度: {len(password) if password else 0} 字符")
        print(f"使用TLS: {use_tls}")
        print()

        # 连接服务器
        print("步骤1: 连接SMTP服务器...")
        if use_tls:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()

        print("  ✓ 连接成功")

        # 登录
        print("步骤2: 登录认证...")
        server.login(sender, password)
        print("  ✓ 登录成功")

        return True, "SMTP连接和认证成功"

    except smtplib.SMTPAuthenticationError as e:
        return False, f"认证失败: {e.smtp_code} - {e.smtp_error.decode()}"
    except smtplib.SMTPConnectError as e:
        return False, f"连接失败: {e}"
    except smtplib.SMTPServerDisconnected as e:
        return False, f"服务器断开连接: {e}"
    except TimeoutError:
        return False, "连接超时，请检查网络或服务器地址"
    except Exception as e:
        return False, f"未知错误: {type(e).__name__}: {e}"
    finally:
        if server:
            try:
                server.quit()
            except:
                pass


def send_test_email(email_config: dict, recipient: str = None) -> tuple:
    """
    发送测试邮件

    Returns:
        (success: bool, message: str)
    """
    server = None
    try:
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 465)
        sender = email_config.get('sender')
        sender_name = email_config.get('sender_name', 'RSS聚合助手')
        password = email_config.get('password')
        use_tls = email_config.get('use_tls', True)

        if not recipient:
            recipient = email_config.get('recipient', sender)

        print(f"收件人: {recipient}")
        print()

        # 构建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{sender_name} <{sender}>"
        msg['To'] = recipient
        msg['Subject'] = f"邮箱连通性测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        text_content = f"""这是一封测试邮件

发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
SMTP服务器: {smtp_server}:{smtp_port}
发件人: {sender}

如果您收到这封邮件，说明SMTP配置正确。

---
RSS聚合助手
"""
        html_content = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2 style="color: #333;">邮箱连通性测试</h2>
<p>这是一封测试邮件</p>
<hr>
<p><strong>发送时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>SMTP服务器:</strong> {smtp_server}:{smtp_port}</p>
<p><strong>发件人:</strong> {sender}</p>
<hr>
<p style="color: #666;">如果您收到这封邮件，说明SMTP配置正确。</p>
<p style="color: #999; font-size: 12px;">— RSS聚合助手</p>
</body>
</html>
"""

        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # 连接并发送
        print("步骤1: 连接SMTP服务器...")
        if use_tls:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
        print("  ✓ 连接成功")

        print("步骤2: 登录认证...")
        server.login(sender, password)
        print("  ✓ 登录成功")

        print("步骤3: 发送邮件...")
        server.sendmail(sender, recipient.split(';')[0].split(',')[0], msg.as_string())
        print("  ✓ 邮件已发送")

        return True, f"测试邮件已发送至 {recipient}"

    except smtplib.SMTPAuthenticationError as e:
        return False, f"认证失败: {e.smtp_code} - {e.smtp_error.decode()}"
    except smtplib.SMTPRecipientsRefused as e:
        return False, f"收件人被拒绝: {e.recipients}"
    except smtplib.SMTPException as e:
        return False, f"SMTP错误: {e}"
    except Exception as e:
        return False, f"未知错误: {type(e).__name__}: {e}"
    finally:
        if server:
            try:
                server.quit()
            except:
                pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description='邮箱连通性测试工具')
    parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')
    parser.add_argument('--send', action='store_true', help='发送测试邮件')
    parser.add_argument('--to', help='指定收件人地址')

    args = parser.parse_args()

    print("=" * 60)
    print("邮箱连通性测试工具")
    print("=" * 60)
    print()

    # 加载配置
    try:
        config = load_config(args.config)
        email_config = config.get('email', {})
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        sys.exit(1)

    if not email_config.get('enabled', False):
        print("⚠️  邮件功能未启用 (email.enabled = false)")
        sys.exit(0)

    print("--- 配置信息 ---")

    if args.send:
        # 发送测试邮件
        print("模式: 发送测试邮件")
        print()
        success, message = send_test_email(email_config, args.to)
    else:
        # 仅测试连接
        print("模式: 仅测试连接（不发送邮件）")
        print()
        success, message = test_smtp_connection(email_config)

    print()
    print("=" * 60)
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()