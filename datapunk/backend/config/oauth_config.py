from pydantic_settings import BaseSettings
from functools import lru_cache

class OAuthSettings(BaseSettings):
    # Local Auth Settings
    # TODO: Generate a secure SECRET_KEY for production
    # Use: python -c 'import secrets; print(secrets.token_hex(32))'
    # Store in .env file as SECRET_KEY=your_generated_key
    SECRET_KEY: str = "development_key"  # CHANGE THIS IN PRODUCTION!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google OAuth Settings
    # TODO: Get these credentials from Google Cloud Console (https://console.cloud.google.com/)
    # 1. Create a new project
    # 2. Enable the Google+ API and Google Drive API
    # 3. Go to Credentials -> Create Credentials -> OAuth Client ID
    # 4. Set up OAuth consent screen
    # 5. Add these to .env as:
    #    GOOGLE_CLIENT_ID=your_client_id
    #    GOOGLE_CLIENT_SECRET=your_client_secret
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # TODO: Update this URL when deploying to production
    # Must match exactly with the redirect URI set in Google Cloud Console
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    
    # These scopes determine what data you can access from Google
    # Add/remove scopes based on your needs from:
    # https://developers.google.com/identity/protocols/oauth2/scopes
    GOOGLE_SCOPES: list = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]
    
    # Microsoft OAuth Settings
    # TODO: Get these credentials from Azure Portal (https://portal.azure.com/)
    # 1. Register a new application in Azure Active Directory
    # 2. Get the client ID and generate a client secret
    # 3. Add these to .env as:
    #    MS_CLIENT_ID=your_client_id
    #    MS_CLIENT_SECRET=your_client_secret
    MS_CLIENT_ID: str = ""
    MS_CLIENT_SECRET: str = ""
    # TODO: Update this URL when deploying to production
    # Must match exactly with the redirect URI set in Azure Portal
    MS_REDIRECT_URI: str = "http://localhost:8000/api/auth/microsoft/callback"
    
    # These scopes determine what data you can access from Microsoft
    # Add/remove scopes based on your needs from:
    # https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent
    MS_SCOPES: list = [
        "User.Read",
        "Mail.Read",
        "Files.Read"
    ]

    class Config:
        # This will load all the above variables from a .env file
        # TODO: Create a .env file in your project root with all the required variables
        # Use .env.example as a template
        env_file = ".env"

@lru_cache()
def get_oauth_settings():
    return OAuthSettings()

