"""Intuit QuickBooks Online OAuth 2.0 and Accounting API Service module for Work-Man's Books.

Supports seamless switching between Sandbox and Live Production environments.
"""

import base64
import json
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


class QuickBooksService:
    # Intuit OAuth 2.0 Endpoints
    OAUTH_AUTHORIZE_URL = "https://appcenter.intuit.com/connect/oauth2"
    OAUTH_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    OAUTH_REVOKE_URL = "https://developer.api.intuit.com/v1/oauth2/tokens/revoke"

    # API Base URLs
    BASE_URLS = {
        "SANDBOX": "https://sandbox-quickbooks.api.intuit.com",
        "PRODUCTION": "https://quickbooks.api.intuit.com",
    }

    # Required Scopes for QuickBooks Accounting Sync
    DEFAULT_SCOPES = ["com.intuit.quickbooks.accounting", "openid"]

    def __init__(
        self,
        environment: str = "SANDBOX",
        client_id: str = "",
        client_secret: str = "",
        redirect_uri: str = "",
    ):
        self.environment = environment.upper() if environment else "SANDBOX"
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.redirect_uri = redirect_uri.strip()

    @property
    def api_base_url(self) -> str:
        return self.BASE_URLS.get(self.environment, self.BASE_URLS["SANDBOX"])

    def _get_basic_auth_header(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    def get_authorization_url(self, state: str = "workmans_books_auth") -> str:
        """Construct Intuit OAuth 2.0 authorization URL for user consent."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(self.DEFAULT_SCOPES),
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        query_string = urllib.parse.urlencode(params)
        return f"{self.OAUTH_AUTHORIZE_URL}?{query_string}"

    def exchange_code_for_tokens(
        self, auth_code: str
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Exchange authorization code for access & refresh tokens."""
        if not self.client_id or not self.client_secret:
            return False, {}, "Client ID and Client Secret are required."

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.strip(),
            "redirect_uri": self.redirect_uri,
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")

        headers = {
            "Authorization": self._get_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        req = urllib.request.Request(
            self.OAUTH_TOKEN_URL, data=data, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                result["expires_at"] = time.time() + result.get("expires_in", 3600)
                return True, result, None
        except urllib.error.HTTPError as error:
            error_msg = error.read().decode("utf-8")
            return False, {}, f"OAuth token exchange failed ({error.code}): {error_msg}"
        except Exception as exc:
            return False, {}, f"Network error during token exchange: {str(exc)}"

    def refresh_access_token(
        self, refresh_token: str
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Refresh expired access token using valid refresh token."""
        if not self.client_id or not self.client_secret:
            return False, {}, "Client ID and Client Secret are required."

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.strip(),
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")

        headers = {
            "Authorization": self._get_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        req = urllib.request.Request(
            self.OAUTH_TOKEN_URL, data=data, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                result["expires_at"] = time.time() + result.get("expires_in", 3600)
                return True, result, None
        except urllib.error.HTTPError as error:
            error_msg = error.read().decode("utf-8")
            return False, {}, f"Token refresh failed ({error.code}): {error_msg}"
        except Exception as exc:
            return False, {}, f"Network error during token refresh: {str(exc)}"

    def revoke_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Revoke active access or refresh token upon disconnect."""
        payload = {"token": token.strip()}
        data = urllib.parse.urlencode(payload).encode("utf-8")

        headers = {
            "Authorization": self._get_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        req = urllib.request.Request(
            self.OAUTH_REVOKE_URL, data=data, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    return True, None
                return False, f"Revocation response code: {response.status}"
        except Exception as exc:
            return False, f"Token revocation error: {str(exc)}"

    def sync_client_to_quickbooks(
        self,
        access_token: str,
        realm_id: str,
        name: str,
        email: str = "",
        phone: str = "",
        address: str = "",
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Create or sync customer in QuickBooks Online."""
        endpoint = f"{self.api_base_url}/v3/company/{realm_id}/customer"

        customer_data = {
            "DisplayName": name,
            "PrimaryEmailAddr": {"Address": email} if email else None,
            "PrimaryPhone": {"FreeFormNumber": phone} if phone else None,
            "BillAddr": {"Line1": address} if address else None,
        }
        # Filter None values
        customer_data = {k: v for k, v in customer_data.items() if v is not None}

        data = json.dumps(customer_data).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return True, res_data, None
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8")
            return False, {}, f"QuickBooks API Error ({error.code}): {error_body}"
        except Exception as exc:
            return False, {}, f"Failed to sync client: {str(exc)}"

    def sync_invoice_to_quickbooks(
        self,
        access_token: str,
        realm_id: str,
        customer_ref_id: str,
        job_title: str,
        amount: float,
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Create invoice in QuickBooks Online."""
        endpoint = f"{self.api_base_url}/v3/company/{realm_id}/invoice"

        invoice_payload = {
            "CustomerRef": {"value": customer_ref_id},
            "Line": [
                {
                    "DetailType": "SalesItemLineDetail",
                    "Amount": amount,
                    "Description": job_title,
                    "SalesItemLineDetail": {
                        "Qty": 1,
                        "UnitPrice": amount,
                    },
                }
            ],
        }

        data = json.dumps(invoice_payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return True, res_data, None
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8")
            return False, {}, f"QuickBooks Invoice API Error ({error.code}): {error_body}"
        except Exception as exc:
            return False, {}, f"Failed to sync invoice: {str(exc)}"
