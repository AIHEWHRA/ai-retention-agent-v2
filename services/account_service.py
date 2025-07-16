# File: services/account_service.py

from services.amp_api_client import AMPApiClient

client = AMPApiClient()

# Lookup user by phone number using /api/get-users-by-phone
def find_user_by_phone(phone_number):
    path = "/api/get-users-by-phone"
    data = {"phone": phone_number}
    return client.tenant_post(path, data)

# Pause membership using impersonation
def pause_membership(user_id):
    path = "/api-user/subscription/pause-vehicle-subscription"
    data = {}
    headers = {
        "Amp-User-Id": user_id,
        "Amp-Account-Id": "USE-DEFAULT-ACCOUNT",
        "Content-Type": "application/json"
    }
    return client.user_patch(path, user_jwt=None, account_id="USE-DEFAULT-ACCOUNT", data=data, custom_headers=headers)

# Cancel membership using impersonation
def cancel_membership(user_id):
    path = "/api-user/subscription/cancel-subscription"
    data = {}
    headers = {
        "Amp-User-Id": user_id,
        "Amp-Account-Id": "USE-DEFAULT-ACCOUNT",
        "Content-Type": "application/json"
    }
    return client.user_patch(path, user_jwt=None, account_id="USE-DEFAULT-ACCOUNT", data=data, custom_headers=headers)

# Downgrade membership plan
def downgrade_membership(user_id, new_plan_id):
    path = "/api-user/subscription/update-vehicle-subscription"
    data = {
        "plan_id": new_plan_id
    }
    headers = {
        "Amp-User-Id": user_id,
        "Amp-Account-Id": "USE-DEFAULT-ACCOUNT",
        "Content-Type": "application/json"
    }
    return client.user_patch(path, user_jwt=None, account_id="USE-DEFAULT-ACCOUNT", data=data, custom_headers=headers)

# Apply credit to user account
def apply_credit(user_id, amount, reason):
    path = "/api-user/credits/apply"
    data = {
        "amount": amount,
        "reason": reason
    }
    headers = {
        "Amp-User-Id": user_id,
        "Amp-Account-Id": "USE-DEFAULT-ACCOUNT",
        "Content-Type": "application/json"
    }
    return client.user_post(path, user_jwt=None, account_id="USE-DEFAULT-ACCOUNT", data=data, custom_headers=headers)

# Get retention offer for user
def get_retention_offer(user_id):
    path = "/api-user/subscription/get-retention-offer"
    data = {}
    headers = {
        "Amp-User-Id": user_id,
        "Amp-Account-Id": "USE-DEFAULT-ACCOUNT",
        "Content-Type": "application/json"
    }
    return client.user_post(path, user_jwt=None, account_id="USE-DEFAULT-ACCOUNT", data=data, custom_headers=headers)

# Respond to retention offer
def respond_retention_offer(user_id, accept_offer):
    path = "/api-user/subscription/respond-retention-offer"
    data = {
        "accept_offer": accept_offer  # Boolean: True to accept, False to decline
    }
    headers = {
        "Amp-User-Id": user_id,
        "Amp-Account-Id": "USE-DEFAULT-ACCOUNT",
        "Content-Type": "application/json"
    }
    return client.user_post(path, user_jwt=None, account_id="USE-DEFAULT-ACCOUNT", data=data, custom_headers=headers)
