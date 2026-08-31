"""
Configuration Module
Centralized configuration and environment variable management
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for application settings"""

    # Slack Configuration
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

    # Salesforce Configuration
    SALESFORCE_INSTANCE_URL = os.environ.get("SALESFORCE_INSTANCE_URL")
    SALESFORCE_CLIENT_ID = os.environ.get("SALESFORCE_CLIENT_ID")
    SALESFORCE_CLIENT_SECRET = os.environ.get("SALESFORCE_CLIENT_SECRET")
    SALESFORCE_USERNAME = os.environ.get("SALESFORCE_USERNAME")
    SALESFORCE_PASSWORD = os.environ.get("SALESFORCE_PASSWORD")

    # Claude AI Configuration
    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
    CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

    # Application Settings
    DEBUG = os.environ.get("DEBUG", "False") == "True"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    @staticmethod
    def validate_config() -> bool:
        """
        Validate that all required configuration variables are set

        Returns:
            True if all required configs are present, False otherwise
        """
        required_vars = [
            "SLACK_BOT_TOKEN",
            "SLACK_APP_TOKEN",
            "SALESFORCE_INSTANCE_URL",
            "SALESFORCE_CLIENT_ID",
            "SALESFORCE_CLIENT_SECRET",
            "SALESFORCE_USERNAME",
            "SALESFORCE_PASSWORD",
            "CLAUDE_API_KEY",
        ]

        missing_vars = [var for var in required_vars if not getattr(Config, var)]

        if missing_vars:
            print(f"❌ Missing required configuration variables: {', '.join(missing_vars)}")
            print("   Please check your .env file")
            return False

        print("✅ All configuration variables loaded successfully")
        return True
