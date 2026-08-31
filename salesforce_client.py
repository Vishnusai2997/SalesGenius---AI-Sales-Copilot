"""
Salesforce API Client Module
Handles authentication and SOQL queries for Salesforce opportunities
"""

import os
import requests
from typing import Optional, Dict, Any


class SalesforceClient:
    """Client for interacting with Salesforce REST API"""

    def __init__(self):
        self.instance_url = os.environ.get("SALESFORCE_INSTANCE_URL")
        self.client_id = os.environ.get("SALESFORCE_CLIENT_ID")
        self.client_secret = os.environ.get("SALESFORCE_CLIENT_SECRET")
        self.username = os.environ.get("SALESFORCE_USERNAME")
        self.password = os.environ.get("SALESFORCE_PASSWORD")
        self.access_token = None

    def authenticate(self) -> bool:
        """Authenticate with Salesforce using OAuth 2.0 password flow"""
        try:
            auth_url = f"{self.instance_url}/services/oauth2/token"
            payload = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password,
            }

            response = requests.post(auth_url, data=payload, timeout=10)
            response.raise_for_status()

            self.access_token = response.json()["access_token"]
            return True
        except Exception as e:
            print(f"Error authenticating with Salesforce: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        if not self.access_token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def query_opportunity(self, opp_id: str) -> Optional[Dict[str, Any]]:
        """Query Salesforce for opportunity details"""
        try:
            soql = f"""SELECT Id, Name, Amount, StageName, CloseDate,
                       Owner.Name, Account.Name, Account.Industry,
                       DaysInStage__c FROM Opportunity WHERE Id = '{opp_id}'"""

            url = f"{self.instance_url}/services/data/v57.0/query"
            params = {"q": soql}

            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            response.raise_for_status()

            records = response.json().get("records", [])
            return records[0] if records else None
        except Exception as e:
            print(f"Error querying Salesforce opportunity: {e}")
            return None

    def create_task(self, opp_id: str, task_subject: str) -> Optional[str]:
        """Create a task in Salesforce linked to an opportunity"""
        try:
            from datetime import datetime, timedelta

            task_data = {
                "Subject": task_subject,
                "WhoId": opp_id,
                "ActivityDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "Status": "Open",
                "Priority": "High"
            }

            url = f"{self.instance_url}/services/data/v57.0/sobjects/Task"
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=task_data,
                timeout=10
            )
            response.raise_for_status()

            return response.json().get("id")
        except Exception as e:
            print(f"Error creating Salesforce task: {e}")
            return None

    def update_opportunity_notes(self, opp_id: str, notes: str) -> bool:
        """Update opportunity description/notes field"""
        try:
            update_data = {"Description": notes}

            url = f"{self.instance_url}/services/data/v57.0/sobjects/Opportunity/{opp_id}"
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=update_data,
                timeout=10
            )
            response.raise_for_status()

            return True
        except Exception as e:
            print(f"Error updating opportunity notes: {e}")
            return False
