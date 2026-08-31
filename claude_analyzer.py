"""
Claude AI Analyzer Module
Handles AI-powered opportunity analysis using Claude API
"""

import json
import os
from typing import Optional, Dict, Any
from anthropic import Anthropic


class OpportunityAnalyzer:
    """Analyzes Salesforce opportunities using Claude AI"""

    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
        self.model = "claude-haiku-4-5-20251001"

    def analyze_opportunity(self, opp_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze an opportunity and return structured insights

        Args:
            opp_data: Dictionary containing opportunity details from Salesforce

        Returns:
            Dictionary with analysis results or None if analysis fails
        """
        try:
            prompt = self._build_analysis_prompt(opp_data)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text

            # Parse JSON response
            try:
                analysis_json = json.loads(analysis_text)
                return analysis_json
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    "score": "N/A",
                    "risk_assessment": analysis_text,
                    "next_steps": "See risk assessment above",
                    "win_strategy": "See risk assessment above"
                }

        except Exception as e:
            print(f"Error analyzing opportunity with Claude: {e}")
            return None

    def _build_analysis_prompt(self, opp_data: Dict[str, Any]) -> str:
        """Build the prompt for Claude analysis"""
        amount = opp_data.get('Amount', 'N/A')
        if isinstance(amount, (int, float)):
            amount_str = f"${amount:,.2f}"
        else:
            amount_str = str(amount)

        prompt = f"""You are a Salesforce sales expert. Analyze this opportunity and provide insights.

Opportunity Data:
- Name: {opp_data.get('Name', 'N/A')}
- Amount: {amount_str}
- Stage: {opp_data.get('StageName', 'N/A')}
- Close Date: {opp_data.get('CloseDate', 'N/A')}
- Account: {opp_data.get('Account', {}).get('Name', 'N/A')}
- Industry: {opp_data.get('Account', {}).get('Industry', 'N/A')}
- Owner: {opp_data.get('Owner', {}).get('Name', 'N/A')}
- Days in Stage: {opp_data.get('DaysInStage__c', 'N/A')}

Provide analysis as JSON with these keys:
1. score (1-10) - likelihood to close
2. risk_assessment - what could go wrong
3. next_steps - what the rep should do TODAY
4. win_strategy - specific plan to close this deal

Return ONLY valid JSON, no additional text."""

        return prompt

    def get_follow_up_action(self, opp_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a specific follow-up action for a sales rep

        Args:
            opp_data: Dictionary containing opportunity details

        Returns:
            A specific action the sales rep should take
        """
        try:
            prompt = f"""Based on this opportunity:
- {opp_data.get('Name', 'Opportunity')}
- Stage: {opp_data.get('StageName', 'N/A')}
- Days in Stage: {opp_data.get('DaysInStage__c', 'N/A')}

Generate ONE specific action the sales rep should take in the next 24 hours.
Be concise (1-2 sentences). No JSON, just plain text."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            print(f"Error generating follow-up action: {e}")
            return None
