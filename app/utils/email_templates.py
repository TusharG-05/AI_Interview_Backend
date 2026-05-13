def get_base_html(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width">
        <meta name="color-scheme" content="dark">
        <meta name="supported-color-schemes" content="dark">
        <title>AI Interview Platform</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0b0f19 !important; font-family: 'Segoe UI', Arial, sans-serif; color: #e2e8f0 !important;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b0f19 !important; min-width: 100%;">
            <tr>
                <td align="center" style="padding: 40px 10px; background-color: #0b0f19 !important;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="width: 600px; max-width: 600px;">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="padding-bottom: 30px;">
                                <div style="color: #818cf8 !important; font-size: 22px; font-weight: bold; letter-spacing: 0.5px;">AI Interview Platform</div>
                            </td>
                        </tr>
                        <!-- Content Area -->
                        <tr>
                            <td>
                                {content}
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td align="center" style="padding-top: 40px; font-size: 11px; color: #4b5563 !important; line-height: 1.6;">
                                <p style="margin: 5px 0;">&copy; 2026 AI Interview Platform. All rights reserved.</p>
                                <p style="margin: 5px 0;">If you did not expect this email, please ignore it.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_invite_template(candidate_name: str, time_str: str, duration_minutes: int, link: str) -> str:
    content = f"""
    <div style="background-color: #111827 !important; border-radius: 16px; padding: 32px; border: 1px solid #1f2937;">
        <h2 style="margin: 0 0 20px 0; color: #ffffff !important; font-size: 22px; font-weight: bold;">Interview Invitation</h2>
        <p style="margin: 0 0 16px 0; line-height: 1.6; font-size: 15px; color: #9ca3af !important;">Hi <strong>{candidate_name}</strong>,</p>
        <p style="margin: 0 0 24px 0; line-height: 1.6; color: #9ca3af !important; font-size: 15px;">You have been invited to an AI-Proctored Interview. Please review the schedule below:</p>
        
        <table width="100%" border="0" cellspacing="0" cellpadding="20" style="background-color: #1f2937 !important; border-radius: 12px; margin-bottom: 32px; border: 1px solid #374151;">
            <tr>
                <td>
                    <div style="font-size: 10px; text-transform: uppercase; color: #6b7280 !important; margin-bottom: 6px; font-weight: bold;">SCHEDULED TIME</div>
                    <div style="font-size: 16px; color: #ffffff !important; font-weight: 600;">{time_str}</div>
                    <div style="height: 20px;"></div>
                    <div style="font-size: 10px; text-transform: uppercase; color: #6b7280 !important; margin-bottom: 6px; font-weight: bold;">DURATION</div>
                    <div style="font-size: 16px; color: #ffffff !important; font-weight: 600;">{duration_minutes} minutes</div>
                </td>
            </tr>
        </table>
        
        <div style="text-align: center;">
            <a href="{link}" style="display: inline-block; background-color: #4f46e5; color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: bold; font-size: 15px;">Start Interview Now</a>
        </div>
    </div>
    """
    return get_base_html(content)

def get_otp_template(otp: str) -> str:
    content = f"""
    <div style="background-color: #111827 !important; border-radius: 16px; padding: 48px; border: 1px solid #1f2937; text-align: center;">
        <h2 style="margin: 0 0 16px 0; color: #ffffff !important; font-size: 24px; font-weight: bold;">Verification Code</h2>
        <p style="margin: 0 0 32px 0; color: #9ca3af !important; font-size: 16px;">Your one-time code to access the platform:</p>
        <div style="background-color: #1f2937 !important; border-radius: 12px; border: 1px solid #374151; padding: 20px; display: inline-block; min-width: 200px;">
            <div style="font-size: 42px; font-weight: bold; letter-spacing: 8px; color: #818cf8 !important;">{otp}</div>
        </div>
    </div>
    """
    return get_base_html(content)

def get_result_template(data: dict) -> str:
    status_icon = "❌" if data['status'].upper() == 'FAIL' else "✅"
    status_color = "#ef4444" if data['status'].upper() == 'FAIL' else "#10b981"
    
    content = f"""
    <p style="margin: 0 0 20px 0; color: #e2e8f0 !important; font-size: 15px;">Hi {data['candidate_name']},</p>
    <p style="margin: 0 0 24px 0; color: #9ca3af !important; font-size: 15px; line-height: 1.6;">Your AI Interview results are now available. Please find your performance summary below:</p>

    <!-- 📊 Candidate Report -->
    <div style="background-color: #111827 !important; border-radius: 12px; padding: 20px; border: 1px solid #1f2937; margin-bottom: 20px;">
        <div style="font-size: 12px; font-weight: bold; color: #818cf8 !important; margin-bottom: 12px; text-transform: uppercase;">📊 Candidate Report</div>
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td>
                    <div style="font-size: 14px; color: #9ca3af !important; margin-bottom: 4px;">Name</div>
                    <div style="font-size: 18px; color: #ffffff !important; font-weight: bold;">{data['candidate_name']}</div>
                </td>
                <td align="right">
                    <div style="font-size: 14px; color: #9ca3af !important; margin-bottom: 4px;">Status</div>
                    <div style="font-size: 16px; color: #818cf8 !important; font-weight: bold;">Completed</div>
                </td>
            </tr>
        </table>
    </div>

    <!-- 📈 Overall Performance -->
    <div style="background-color: #111827 !important; border-radius: 12px; padding: 20px; border: 1px solid #1f2937; margin-bottom: 20px;">
        <div style="font-size: 12px; font-weight: bold; color: #818cf8 !important; margin-bottom: 15px; text-transform: uppercase;">📈 Overall Performance</div>
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td width="48%">
                    <div style="font-size: 13px; color: #9ca3af !important;">Score</div>
                    <div style="font-size: 20px; color: #ffffff !important; font-weight: bold; margin-top: 5px;">{data['score']} / {data['max_score']}</div>
                </td>
                <td width="4%"></td>
                <td width="48%">
                    <div style="font-size: 13px; color: #9ca3af !important;">Result Status</div>
                    <div style="font-size: 20px; color: {status_color} !important; font-weight: bold; margin-top: 5px;">{status_icon} {data['status']}</div>
                </td>
            </tr>
        </table>
    </div>

    <!-- 🧠 Assessment Details -->
    <div style="background-color: #111827 !important; border-radius: 12px; padding: 20px; border: 1px solid #1f2937; margin-bottom: 20px;">
        <div style="font-size: 12px; font-weight: bold; color: #818cf8 !important; margin-bottom: 15px; text-transform: uppercase;">🧠 Assessment Details</div>
        <div style="margin-bottom: 10px;">
            <span style="color: #9ca3af !important; font-size: 14px;">Theory Sections:</span>
            <span style="color: #ffffff !important; font-size: 14px; font-weight: 600; margin-left: 8px;">{data['theory_count']} questions attempted</span>
        </div>
        <div>
            <span style="color: #9ca3af !important; font-size: 14px;">Coding Challenges:</span>
            <span style="color: #ffffff !important; font-size: 14px; font-weight: 600; margin-left: 8px;">{data['coding_count']} challenges attempted</span>
        </div>
    </div>

    <!-- 🗂️ Session Details -->
    <div style="background-color: #111827 !important; border-radius: 12px; padding: 20px; border: 1px solid #1f2937; margin-bottom: 25px;">
        <div style="font-size: 12px; font-weight: bold; color: #818cf8 !important; margin-bottom: 15px; text-transform: uppercase;">🗂️ Session Details</div>
        <table width="100%" border="0" cellspacing="0" cellpadding="8">
            <tr>
                <td width="50%" style="border-bottom: 1px solid #1f2937;">
                    <div style="font-size: 11px; color: #4b5563 !important;">Interviewer</div>
                    <div style="font-size: 13px; color: #e2e8f0 !important;">{data['admin_name']}</div>
                </td>
                <td width="50%" style="border-bottom: 1px solid #1f2937;">
                    <div style="font-size: 11px; color: #4b5563 !important;">Interview Round</div>
                    <div style="font-size: 13px; color: #e2e8f0 !important;">{data['round_name']}</div>
                </td>
            </tr>
            <tr>
                <td width="50%" style="border-bottom: 1px solid #1f2937;">
                    <div style="font-size: 11px; color: #4b5563 !important;">Scheduled Time</div>
                    <div style="font-size: 13px; color: #e2e8f0 !important;">{data['scheduled_time']}</div>
                </td>
                <td width="50%" style="border-bottom: 1px solid #1f2937;">
                    <div style="font-size: 11px; color: #4b5563 !important;">Start Time</div>
                    <div style="font-size: 13px; color: #e2e8f0 !important;">{data.get('start_time', 'N/A')}</div>
                </td>
            </tr>
            <tr>
                <td width="50%">
                    <div style="font-size: 11px; color: #4b5563 !important;">Duration</div>
                    <div style="font-size: 13px; color: #e2e8f0 !important;">{data['duration_mins']} minutes</div>
                </td>
                <td width="50%">
                    <div style="font-size: 11px; color: #4b5563 !important;">Proctoring Warnings</div>
                    <div style="font-size: 13px; color: #e2e8f0 !important;">{data.get('proctoring_warnings', '0 / 3')}</div>
                </td>
            </tr>
        </table>
    </div>

    <p style="margin: 0 0 20px 0; color: #9ca3af !important; font-size: 14px; line-height: 1.5;">
        If you believe this result is incorrect or need assistance, please contact the support team.
    </p>
    <p style="margin: 0; color: #e2e8f0 !important; font-size: 15px; font-weight: bold;">
        Best regards,<br>
        <span style="color: #818cf8 !important;">AI Interview Platform Team</span>
    </p>
    """
    return get_base_html(content)
