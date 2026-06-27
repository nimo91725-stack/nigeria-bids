import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from .config import settings
from .models import Opportunity, AlertConfig

logger = logging.getLogger(__name__)


def _matches(opp: Opportunity, keywords: str) -> bool:
    text = f"{opp.title} {opp.description or ''} {opp.organization}".lower()
    return any(kw.strip().lower() in text for kw in keywords.split(","))


def _build_email(new_opps: list[Opportunity], recipient_email: str) -> MIMEMultipart:
    today = datetime.now().strftime("%d %b %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Nigeria Bids — {len(new_opps)} New Opportunities ({today})"
    msg["From"] = settings.alert_from_email
    msg["To"] = recipient_email

    # Plain text
    lines = [f"Nigeria Bids Daily Alert — {today}\n"]
    lines.append(f"{len(new_opps)} new travel management bid(s) found:\n")
    for opp in new_opps:
        deadline = opp.deadline.strftime("%d %b %Y") if opp.deadline else "No deadline listed"
        lines.append(f"• {opp.title}")
        lines.append(f"  Organisation: {opp.organization}")
        lines.append(f"  Sector:       {opp.sector or '—'}")
        lines.append(f"  Source:       {opp.source_name or opp.source_type}")
        lines.append(f"  Deadline:     {deadline}")
        if opp.source_url:
            lines.append(f"  Link:         {opp.source_url}")
        lines.append("")
    lines.append("View all bids: https://nigeria-bids-frontend-wmyc45oroq-bq.a.run.app")
    text_body = "\n".join(lines)

    # HTML
    rows = ""
    for opp in new_opps:
        deadline = opp.deadline.strftime("%d %b %Y") if opp.deadline else "—"
        link = f'<a href="{opp.source_url}">View Tender</a>' if opp.source_url else "—"
        rows += f"""
        <tr>
          <td style="padding:10px 8px;border-bottom:1px solid #e5e7eb">
            <strong style="color:#15803d">{opp.title}</strong><br>
            <span style="color:#6b7280;font-size:13px">{opp.organization}</span>
          </td>
          <td style="padding:10px 8px;border-bottom:1px solid #e5e7eb;color:#374151;font-size:13px">{opp.sector or '—'}</td>
          <td style="padding:10px 8px;border-bottom:1px solid #e5e7eb;color:#374151;font-size:13px">{opp.source_name or opp.source_type}</td>
          <td style="padding:10px 8px;border-bottom:1px solid #e5e7eb;color:#374151;font-size:13px">{deadline}</td>
          <td style="padding:10px 8px;border-bottom:1px solid #e5e7eb;font-size:13px">{link}</td>
        </tr>"""

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f9fafb;margin:0;padding:20px">
      <div style="max-width:700px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)">
        <div style="background:#15803d;padding:24px 28px">
          <h1 style="margin:0;color:#fff;font-size:20px">Nigeria Bids — Daily Alert</h1>
          <p style="margin:6px 0 0;color:#bbf7d0;font-size:14px">{today} &nbsp;·&nbsp; {len(new_opps)} new opportunity(s)</p>
        </div>
        <div style="padding:24px 28px">
          <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-size:14px">
            <thead>
              <tr style="background:#f3f4f6;color:#6b7280;font-size:12px;text-transform:uppercase">
                <th style="padding:8px;text-align:left">Title / Organisation</th>
                <th style="padding:8px;text-align:left">Sector</th>
                <th style="padding:8px;text-align:left">Source</th>
                <th style="padding:8px;text-align:left">Deadline</th>
                <th style="padding:8px;text-align:left">Link</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
          <div style="margin-top:24px;text-align:center">
            <a href="https://nigeria-bids-frontend-wmyc45oroq-bq.a.run.app"
               style="background:#15803d;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px">
              View All Bids on Dashboard
            </a>
          </div>
        </div>
        <div style="padding:16px 28px;background:#f9fafb;color:#9ca3af;font-size:12px;text-align:center">
          Nigeria Bids Aggregator &nbsp;·&nbsp; Travel Management Services
        </div>
      </div>
    </body></html>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


async def send_daily_alerts(new_opps: list[Opportunity], alert_configs: list[AlertConfig]) -> dict:
    if not settings.smtp_host or not new_opps:
        return {"sent": 0, "skipped": 0}

    sent, skipped = 0, 0
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)

            for config in alert_configs:
                if not config.active:
                    continue
                matching = [o for o in new_opps if _matches(o, config.keywords)]
                if not matching:
                    skipped += 1
                    continue
                try:
                    msg = _build_email(matching, config.email)
                    server.sendmail(settings.alert_from_email, config.email, msg.as_string())
                    sent += 1
                    logger.info(f"Alert sent to {config.email} with {len(matching)} opportunities")
                except Exception as e:
                    logger.error(f"Failed to send alert to {config.email}: {e}")
                    skipped += 1
    except Exception as e:
        logger.error(f"SMTP connection failed: {e}")

    return {"sent": sent, "skipped": skipped}
