
import falcon
import jwt
import requests
from jwt import PyJWKClient
from utils.config import APPLE_SIGN_IN_AUD

APPLE_AUTH_KEYS_URL = 'https://appleid.apple.com/auth/keys'


def verify_id_token(id_token: str, bundle_id=None) -> dict:

    if bundle_id is None:
        bundle_id = APPLE_SIGN_IN_AUD[0]
    if bundle_id not in APPLE_SIGN_IN_AUD:
        raise falcon.HTTPForbidden(description="Not allow bundle id.")

    jwt_header = jwt.get_unverified_header(id_token)

    # get kid to select public key
    kid = jwt_header.get("kid", None)
    if kid is None:
        raise falcon.HTTPUnauthorized(
            description="Not found kid from your id_token, check your token is by apple sign in."
        )

    jwks_client = PyJWKClient(APPLE_AUTH_KEYS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)

    jwt_decode = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=bundle_id,
        options={"verify_exp": False},
    )
    return jwt_decode
