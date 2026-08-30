from odoo import api, models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """Link a verified Google identity to an existing EcoSphere account.

        OAuth must never turn an arbitrary Google account into an EcoSphere user.
        Administrators still control access through enterprise signup and Team access.
        """
        oauth_uid = validation.get("user_id")
        oauth_user = self.search([
            ("oauth_uid", "=", oauth_uid),
            ("oauth_provider_id", "=", provider),
        ], limit=1)
        if oauth_user:
            oauth_user.write({"oauth_access_token": params["access_token"]})
            return oauth_user.login

        google_provider = self.env.ref("auth_oauth.provider_google", raise_if_not_found=False)
        verified = validation.get("email_verified") in (True, "true", "True", 1, "1")
        email = (validation.get("email") or "").strip().lower()
        if google_provider and provider == google_provider.id and verified and email:
            matching_users = self.search([("login", "=ilike", email), ("active", "=", True)], limit=2)
            if len(matching_users) == 1 and not matching_users.oauth_provider_id:
                matching_users.write({
                    "oauth_provider_id": provider,
                    "oauth_uid": oauth_uid,
                    "oauth_access_token": params["access_token"],
                })
                return matching_users.login

        # The provider state sets no_user_creation. Keep the standard behavior for
        # already-linked identities while refusing unprovisioned Google accounts.
        try:
            return super()._auth_oauth_signin(provider, validation, params)
        except AccessDenied:
            raise
