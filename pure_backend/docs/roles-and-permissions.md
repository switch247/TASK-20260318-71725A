# Roles and Permissions

Roles:

- `administrator`: full management permissions
- `reviewer`: workflow review + analytics read + export request
- `general_user`: process create + analytics read + export request
- `auditor`: audit read + analytics read + export read

Authorization model:

- Every protected request validates organization membership
- Resource-action permissions are evaluated per role
- Non-members and unauthorized roles receive `403`
