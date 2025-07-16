# File: services/amp_api_client.py

import requests
import os

class AMPApiClient:
    def __init__(self):
        self.base_url = "https://api.ampmemberships.com"
        self.tenant_key = os.getenv("AMP_TENANT", "HURRICANE")
        self.tenant_api_key = os.getenv("AMP_TENANT_API", "api_1270ffa2a23b493fb78a46feb26215c6")
        self.headers = {
            "Amp-Tenant": self.tenant_key,
            "Amp-Tenant-Api": self.tenant_api_key,
            "Content-Type": "application/json"
        }

    def _handle_response(self, response):
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ AMP API Error: {response.status_code} - {response.text}")
            return None

    def tenant_get(self, path):
        url = f"{self.base_url}{path}"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)

    def tenant_patch(self, path, data=None):
        url = f"{self.base_url}{path}"
        response = requests.patch(url, headers=self.headers, json=data)
        return self._handle_response(response)

    def tenant_post(self, path, data=None):
        url = f"{self.base_url}{path}"
        response = requests.post(url, headers=self.headers, json=data)
        return self._handle_response(response)

    def user_auth_sign_in(self, username, password):
        url = f"{self.base_url}/api/auth/sign-in"
        data = {"username": username, "password": password}
        response = requests.post(url, headers=self.headers, json=data)
        return self._handle_response(response)

    def user_post(self, path, user_jwt, account_id, data=None):
        user_headers = {
            "Authorization": f"Bearer {user_jwt}",
            "Amp-Account-Id": account_id,
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}{path}"
        response = requests.post(url, headers=user_headers, json=data)
        return self._handle_response(response)

    def user_patch(self, path, user_jwt, account_id, data=None):
        user_headers = {
            "Authorization": f"Bearer {user_jwt}",
            "Amp-Account-Id": account_id,
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}{path}"
        response = requests.patch(url, headers=user_headers, json=data)
        return self._handle_response(response)
