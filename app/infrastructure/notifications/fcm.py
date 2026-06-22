import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

_app = None


def _get_app():
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _app = firebase_admin.initialize_app(cred)
    return _app


async def send_push(token: str, title: str, body: str, data: dict | None = None) -> bool:
    try:
        _get_app()
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        messaging.send(message)
        return True
    except Exception:
        return False


async def send_push_multicast(tokens: list[str], title: str, body: str, data: dict | None = None) -> None:
    if not tokens:
        return
    try:
        _get_app()
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )
        messaging.send_each_for_multicast(message)
    except Exception:
        pass
