import os
import json
from typing import Dict, Any, Optional
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider implementation.
    Uses google-generativeai package.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro", **kwargs):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        # Handle 'model' kwarg if passed (from config/factory)
        self.model_name = kwargs.get("model", model_name)
        self.oauth_client_secret = kwargs.get("oauth_client_secret")
        self.oauth_token_path = kwargs.get("oauth_token_path")
        self.credentials = None
        
        if not self.api_key and self.oauth_client_secret:
             print(" Starting Gemini OAuth authentication flow...")
             self.credentials = self._authenticate_oauth()

        if not self.api_key and not self.credentials:
            print(" Warning: GOOGLE_API_KEY and OAuth credentials not found. GeminiProvider will run in simulation mode.")
            self.simulated = True
        else:
            self.simulated = False
            import google.generativeai as genai
            if self.credentials:
                genai.configure(credentials=self.credentials)
            else:
                genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

    def _authenticate_oauth(self):
        """Authenticate using standard Google OAuth flow."""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
        except ImportError:
            print(" Error: google-auth-oauthlib or google-auth not installed.")
            return None

        scopes = ['https://www.googleapis.com/auth/generative-language']
        creds = None
        token_path = Path(self.oauth_token_path)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(self.oauth_client_secret).exists():
                    print(f" Error: Client secret file not found at {self.oauth_client_secret}")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(self.oauth_client_secret, scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return creds

    def generate_response(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.7) -> str:
        if self.simulated:
            return f"[SIMULATED GEMINI RESPONSE for: {prompt[:50]}...]"
        
        # Real implementation using genai.GenerativeModel
        return "Not implemented in this environment yet."

    def generate_json(self, prompt: str, schema: Dict[str, Any], system_instruction: Optional[str] = None) -> Dict[str, Any]:
        if self.simulated:
            # Return a minimal valid structure based on schema keys if possible
            return {k: f"mock_{k}" for k in schema.get("properties", {})}
        
        return {}
