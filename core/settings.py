import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load the project .env for local development. Render variables override it.
load_dotenv(override=False)


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def get_organisation_invite_code() -> str:
    """Resolve the current invite code with backward compatibility.

    ORGANISATION_INVITE_CODE is the preferred name. The older
    MINISTRY_INVITE_CODE remains supported so existing deployments continue
    working. The local development fallback is DATADEV.
    """
    return (
        _clean(os.getenv("ORGANISATION_INVITE_CODE"))
        or _clean(os.getenv("MINISTRY_INVITE_CODE"))
        or "DATADEV"
    )


def invite_code_matches(submitted_code: str | None) -> bool:
    submitted = _clean(submitted_code).casefold()
    configured = get_organisation_invite_code().casefold()
    return bool(submitted) and submitted == configured


@dataclass(frozen=True)
class StartupStatus:
    database_backend: str
    app_base_url: str
    invite_source: str
    qr_key_configured: bool


def get_invite_source() -> str:
    if _clean(os.getenv("ORGANISATION_INVITE_CODE")):
        return "ORGANISATION_INVITE_CODE"
    if _clean(os.getenv("MINISTRY_INVITE_CODE")):
        return "MINISTRY_INVITE_CODE (legacy compatibility)"
    return "built-in local fallback"
