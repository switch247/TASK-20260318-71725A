# Roles and Permissions

The platform implements four operational roles:

## 1) administrator

- Full organization-level management
- Can manage identity and organization data
- Can create/manage process definitions and workflows
- Can access analytics and request/manage exports
- Can manage governance operations and read audit domain

## 2) reviewer

- Can review and decide process tasks
- Can read analytics
- Can request exports
- Cannot manage identity/org or process definitions

## 3) general_user

- Can submit process instances
- Can read analytics
- Can request exports
- Cannot review tasks or manage governance

## 4) auditor

- Can read audit domain
- Can read analytics
- Can read export information
- Cannot create process instances or manage workflows

## Enforcement Model

- Permission checks are resource-action based
- Role grants are persisted in `role_permissions`
- Organization membership is enforced per request via `X-Organization-Id`
- Requests from non-members are denied, even with a valid token
