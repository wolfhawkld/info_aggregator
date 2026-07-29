# -*- coding: utf-8 -*-
"""
邮件通知模块 - 发送每日摘要邮件
"""

import os
import re
import smtplib
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# 匹配有序列表前缀，如 "1. "、"12. "
_ORDERED_LIST_RE = re.compile(r'^\d+\.\s+(.*)$')


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config: Dict):
        """
        初始化邮件通知器

        Args:
            config: 邮件配置字典
        """
        self.enabled = config.get('enabled', False)
        self.smtp_server = config.get('smtp_server', 'smtp.163.com')
        self.smtp_port = config.get('smtp_port', 465)
        self.sender = config.get('sender', '')
        self.sender_name = config.get('sender_name', 'RSS聚合助手')
        self.use_tls = config.get('use_tls', True)

        # 优先从配置文件读取密码，否则从环境变量获取
        self.password = config.get('password', '') or os.environ.get('EMAIL_PASSWORD', '')

        # 调试日志：打印实际读取的配置
        logger.info(f"邮件配置读取: server={self.smtp_server}, port={self.smtp_port}, sender={self.sender}")
        logger.info(f"密码已设置: {'是' if self.password else '否'}")

        if self.enabled and not self.password:
            logger.warning("邮件功能已启用但未设置密码（配置文件或EMAIL_PASSWORD环境变量）")

    def send_daily_summary(
        self,
        brief_summary: str,
        recipient: str,
        date_str: str,
        stats: Dict
    ) -> bool:
        """
        发送每日摘要邮件

        Args:
            brief_summary: 一句话精简摘要
            recipient: 收件人邮箱
            date_str: 日期字符串
            stats: 统计信息字典

        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.info("邮件功能未启用，跳过发送")
            return False

        if not self.password:
            logger.error("未设置密码，无法发送邮件")
            return False

        # 解析多个收件人（支持分号或逗号分隔）
        recipients = [r.strip() for r in recipient.replace(',', ';').split(';') if r.strip()]

        try:
            # 构建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.sender_name, self.sender))
            msg['To'] = ', '.join(recipients)  # 显示所有收件人
            msg['Subject'] = f"[每日摘要] {date_str} - AI研究动态"

            # 纯文本版本
            text_content = self._build_text_content(brief_summary, date_str, stats)

            # HTML版本
            html_content = self._build_html_content(brief_summary, date_str, stats)

            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 发送邮件 - 465端口使用SMTP_SSL，其他端口使用SMTP+STARTTLS
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender, self.password)
                    server.sendmail(self.sender, recipients, msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.sender, self.password)
                    server.sendmail(self.sender, recipients, msg.as_string())

            logger.info(f"邮件发送成功: {', '.join(recipients)}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}", exc_info=True)
            return False

    def _build_text_content(
        self,
        brief_summary: str,
        date_str: str,
        stats: Dict
    ) -> str:
        """构建纯文本邮件内容"""
        web_url = stats.get('web_url', '')

        content = f"""每日AI研究摘要 - {date_str}

{brief_summary}

---
统计信息:
- RSS文章数: {stats.get('rss_articles', 0)}
- 探索主题数: {stats.get('exploration_count', 0)}

"""
        if web_url:
            content += f"""详细内容链接:
{web_url}/index.html

"""
        content += "此邮件由RSS聚合助手自动生成"
        return content

    def _build_html_content(
        self,
        brief_summary: str,
        date_str: str,
        stats: Dict
    ) -> str:
        """构建HTML邮件内容"""
        # 将 markdown bullet points 转换为 HTML 列表
        summary_html = self._format_summary_to_html(brief_summary)
        web_url = stats.get('web_url', '')

        # 构建链接区域
        link_section = ""
        if web_url:
            link_section = f"""
    <div class="link-section" style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
        <p style="margin: 0 0 10px 0; font-weight: bold; color: #0078d4;">查看详细内容</p>
        <a href="{web_url}/index.html" style="display: inline-block; background: #0078d4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
            点击查看每日汇总
        </a>
        <p style="margin: 10px 0 0 0; font-size: 12px; color: #666;">
            包含RSS摘要及5个主题探索的完整内容
        </p>
    </div>
"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #0078d4; padding-bottom: 10px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .summary ul {{ margin: 0; padding-left: 20px; }}
        .summary li {{ margin-bottom: 8px; font-size: 16px; }}
        .stats {{ color: #666; font-size: 14px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>每日AI研究摘要</h1>
    <p style="color: #666;">{date_str}</p>

    <div class="summary">
        {summary_html}
    </div>

    {link_section}

    <div class="stats">
        <p><strong>统计信息:</strong></p>
        <ul>
            <li>RSS文章数: {stats.get('rss_articles', 0)}</li>
            <li>探索主题数: {stats.get('exploration_count', 0)}</li>
        </ul>
    </div>

    <div class="footer">
        此邮件由RSS聚合助手自动生成
    </div>
</body>
</html>
"""
        return html

    def _format_summary_to_html(self, summary: str) -> str:
        """将 markdown 要点转换为 HTML 列表。

        支持 -、• 以及 1. 2. 等有序列表前缀，统一渲染为无序列表，
        避免 LLM 把所有项都标为 1 导致邮件里序号错乱。
        """
        if not summary or not summary.strip():
            return '<p>（无摘要内容）</p>'

        lines = summary.strip().split('\n')
        html_lines = []
        in_list = False

        def close_list():
            nonlocal in_list
            if in_list:
                html_lines.append('</ul>')
                in_list = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue  # 空行不中断列表

            content = None
            if stripped.startswith('- ') or stripped.startswith('• '):
                content = stripped[2:]
            else:
                m = _ORDERED_LIST_RE.match(stripped)
                if m:
                    content = m.group(1)

            if content is not None:
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{escape(content)}</li>')
            else:
                close_list()
                html_lines.append(f'<p>{escape(stripped)}</p>')

        close_list()
        return '\n'.join(html_lines)