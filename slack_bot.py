"""
Salesforce AI Sales Assistant - Slack Bot
Integrates Salesforce CRM with Claude AI for intelligent opportunity analysis
"""

import os
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from anthropic import Anthropic
import requests
from datetime import datetime, timedelta

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
client = Anthropic()

# Salesforce credentials
SALESFORCE_INSTANCE_URL = os.environ.get("SALESFORCE_INSTANCE_URL")
SALESFORCE_CLIENT_ID = os.environ.get("SALESFORCE_CLIENT_ID")
SALESFORCE_CLIENT_SECRET = os.environ.get("SALESFORCE_CLIENT_SECRET")
SALESFORCE_USERNAME = os.environ.get("SALESFORCE_USERNAME")
SALESFORCE_PASSWORD = os.environ.get("SALESFORCE_PASSWORD")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

# Store access token
sf_access_token = None


def get_salesforce_token():
    """Get Salesforce OAuth access token"""
    global sf_access_token

    try:
        auth_url = f"{SALESFORCE_INSTANCE_URL}/services/oauth2/token"
        payload = {
            "grant_type": "password",
            "client_id": SALESFORCE_CLIENT_ID,
            "client_secret": SALESFORCE_CLIENT_SECRET,
            "username": SALESFORCE_USERNAME,
            "password": SALESFORCE_PASSWORD,
        }

        response = requests.post(auth_url, data=payload)
        response.raise_for_status()
        sf_access_token = response.json()["access_token"]
        return sf_access_token
    except Exception as e:
        print(f"Error getting Salesforce token: {e}")
        return None


def query_salesforce_opportunity(opp_id):
    """Query Salesforce for opportunity details"""
    try:
        if not sf_access_token:
            get_salesforce_token()

        headers = {
            "Authorization": f"Bearer {sf_access_token}",
            "Content-Type": "application/json",
        }

        soql = f"""SELECT Id, Name, Amount, StageName, CloseDate,
                   Owner.Name, Account.Name, Account.Industry,
                   DaysInStage__c FROM Opportunity WHERE Id = '{opp_id}'"""

        url = f"{SALESFORCE_INSTANCE_URL}/services/data/v57.0/query"
        params = {"q": soql}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        records = response.json().get("records", [])
        if records:
            return records[0]
        return None
    except Exception as e:
        print(f"Error querying Salesforce: {e}")
        return None


def analyze_opportunity_with_claude(opp_data):
    """Send opportunity data to Claude for analysis"""
    try:
        prompt = f"""You are a Salesforce sales expert. Analyze this opportunity and provide:
1. Deal Score (1-10) - likelihood to close
2. Risk Assessment - what could go wrong
3. Next Steps - what the rep should do TODAY
4. Win Strategy - specific plan to close this deal

Opportunity Data:
- Name: {opp_data.get('Name', 'N/A')}
- Amount: ${opp_data.get('Amount', 'N/A'):,}
- Stage: {opp_data.get('StageName', 'N/A')}
- Close Date: {opp_data.get('CloseDate', 'N/A')}
- Account: {opp_data.get('Account', {}).get('Name', 'N/A')}
- Industry: {opp_data.get('Account', {}).get('Industry', 'N/A')}
- Owner: {opp_data.get('Owner', {}).get('Name', 'N/A')}

Format your response as JSON with keys: score, risk_assessment, next_steps, win_strategy"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"Error analyzing with Claude: {e}")
        return None


def create_salesforce_task(opp_id, task_name):
    """Create a task in Salesforce"""
    try:
        if not sf_access_token:
            get_salesforce_token()

        headers = {
            "Authorization": f"Bearer {sf_access_token}",
            "Content-Type": "application/json",
        }

        task_data = {
            "Subject": task_name,
            "WhoId": opp_id,
            "ActivityDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "Status": "Open",
            "Priority": "High"
        }

        url = f"{SALESFORCE_INSTANCE_URL}/services/data/v57.0/sobjects/Task"
        response = requests.post(url, headers=headers, json=task_data)
        response.raise_for_status()

        return response.json().get("id")
    except Exception as e:
        print(f"Error creating task: {e}")
        return None


@app.event("app_mention")
def handle_mention(event, say):
    """Handle @sales-assistant mentions"""
    try:
        text = event.get("text", "").strip()

        # Extract opportunity ID from message
        # Format: @sales-assistant analyze 006XX000001SGVQAA2
        parts = text.split()

        if len(parts) < 3:
            say("Please use: @sales-assistant analyze [opportunity-id]")
            return

        opp_id = parts[2]

        # Show loading message
        say(f"🔍 Analyzing opportunity {opp_id}...")

        # Query Salesforce
        opp_data = query_salesforce_opportunity(opp_id)
        if not opp_data:
            say(f"❌ Could not find opportunity {opp_id}")
            return

        # Analyze with Claude
        analysis = analyze_opportunity_with_claude(opp_data)

        # Parse and format response
        try:
            analysis_json = json.loads(analysis)
            score = analysis_json.get("score", "N/A")
            risk = analysis_json.get("risk_assessment", "N/A")
            next_steps = analysis_json.get("next_steps", "N/A")
            strategy = analysis_json.get("win_strategy", "N/A")
        except:
            # Fallback if JSON parsing fails
            say(f"```{analysis}```")
            return

        # Send formatted response with interactive buttons
        say(
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Deal Analysis: {opp_data.get('Name', 'Opportunity')}",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Deal Score:* {score}/10\n*Amount:* ${opp_data.get('Amount', 'N/A'):,}\n*Stage:* {opp_data.get('StageName', 'N/A')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*⚠️ Risk Assessment:*\n{risk}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📋 Next Steps:*\n{next_steps}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🎯 Win Strategy:*\n{strategy}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Create Task"
                            },
                            "action_id": "create_task",
                            "value": opp_id,
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Update Notes"
                            },
                            "action_id": "update_notes",
                            "value": opp_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📅 Schedule Follow-up"
                            },
                            "action_id": "schedule_event",
                            "value": opp_id
                        }
                    ]
                }
            ]
        )

    except Exception as e:
        say(f"❌ Error: {str(e)}")


@app.action("create_task")
def handle_create_task(ack, body, say):
    """Handle create task button click"""
    ack()

    opp_id = body["actions"][0]["value"]
    task_id = create_salesforce_task(opp_id, "Follow up on opportunity")

    if task_id:
        say(f"✅ Task created successfully! Task ID: {task_id}")
    else:
        say("❌ Failed to create task")


@app.action("update_notes")
def handle_update_notes(ack, body, say):
    """Handle update notes button click"""
    ack()
    say("📝 Note update feature coming soon!")


@app.action("schedule_event")
def handle_schedule_event(ack, body, say):
    """Handle schedule event button click"""
    ack()
    say("📅 Event scheduling feature coming soon!")


if __name__ == "__main__":
    # Start the bot
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    print("⚡️ Bolt app is running!")
    handler.start()
