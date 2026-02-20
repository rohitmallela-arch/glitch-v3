from __future__ import annotations

from typing import Any, Dict, Optional, List
import time
import hashlib

from google.cloud.firestore import Client
from google.cloud import firestore

from storage.firestore_client import get_firestore_client

COL_AUTH_CHALLENGES = "auth_challenges"
COL_AUTH_SESSIONS = "auth_sessions"
COL_USERS = "users"

# Guards (fail-closed)
AUTH_CHALLENGE_COOLDOWN_SEC = 60
AUTH_MAX_OUTSTANDING_CHALLENGES = 3


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _clean_active(active: Any, now: int) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    if not isinstance(active, list):
        return cleaned
    for it in active:
        if not isinstance(it, dict):
            continue
        cid = str(it.get("challenge_id") or "")
        try:
            exp = int(it.get("expires_at") or 0)
        except Exception:
            continue
        if cid and exp > now:
            cleaned.append({"challenge_id": cid, "expires_at": exp})
    return cleaned


class AuthRepository:
    """
    Reverse-OTP auth via inbound SMS + server-issued bearer sessions.

    Challenge doc id = sha256_hex(code)
    Session doc id   = sha256_hex(token)

    Cooldown + outstanding cap are enforced on users/{user_id}:
      - auth_last_challenge_at: int epoch sec
      - auth_active_challenges: list of {challenge_id, expires_at}
    """

    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    # -------- Challenges --------
    def create_challenge(self, phone_e164: str, user_id: str, code: str, ttl_sec: int) -> Dict[str, Any]:
        """
        Create a challenge with cooldown + outstanding cap enforced.

        Fail-closed: raises ValueError with one of:
          - user_not_found
          - cooldown_active
          - too_many_outstanding
        """
        now = int(time.time())
        challenge_id = _sha256_hex(code)
        expires_at = now + int(ttl_sec)

        user_ref = self.db.collection(COL_USERS).document(user_id)
        ch_ref = self.db.collection(COL_AUTH_CHALLENGES).document(challenge_id)

        txn = self.db.transaction()

        @firestore.transactional
        def _run(tx: firestore.Transaction) -> Dict[str, Any]:
            user_snap = user_ref.get(transaction=tx)
            if not user_snap.exists:
                raise ValueError("user_not_found")

            u = user_snap.to_dict() or {}
            last = int(u.get("auth_last_challenge_at") or 0)
            if last and (now - last) < AUTH_CHALLENGE_COOLDOWN_SEC:
                raise ValueError("cooldown_active")

            active = _clean_active(u.get("auth_active_challenges"), now)
            if len(active) >= AUTH_MAX_OUTSTANDING_CHALLENGES:
                raise ValueError("too_many_outstanding")

            payload = {
                "phone_e164": phone_e164,
                "user_id": user_id,
                "code_hash": challenge_id,
                "expires_at": expires_at,
                "verified_at": None,
                "consumed_at": None,
                "created_at": firestore.SERVER_TIMESTAMP,
            }

            # deterministic id for inbound lookup; overwrite is fine (code random)
            tx.set(ch_ref, payload, merge=False)

            active.append({"challenge_id": challenge_id, "expires_at": expires_at})
            tx.set(
                user_ref,
                {"auth_last_challenge_at": now, "auth_active_challenges": active},
                merge=True,
            )

            return {"challenge_id": challenge_id, **payload}

        return _run(txn)

    def get_challenge_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        challenge_id = _sha256_hex(code)
        snap = self.db.collection(COL_AUTH_CHALLENGES).document(challenge_id).get()
        if not snap.exists:
            return None
        d = snap.to_dict() or {}
        d["challenge_id"] = challenge_id
        return d

    def mark_verified(self, challenge_id: str, from_phone_e164: str) -> None:
        ref = self.db.collection(COL_AUTH_CHALLENGES).document(challenge_id)
        ref.set(
            {
                "verified_at": int(time.time()),
                "last_from_phone": from_phone_e164,
            },
            merge=True,
        )

    def mark_consumed(self, challenge_id: str) -> None:
        now = int(time.time())
        ch_ref = self.db.collection(COL_AUTH_CHALLENGES).document(challenge_id)

        snap = ch_ref.get()
        if snap.exists:
            d = snap.to_dict() or {}
            user_id = str(d.get("user_id") or "")
            if user_id:
                user_ref = self.db.collection(COL_USERS).document(user_id)
                try:
                    u = user_ref.get().to_dict() or {}
                    active = _clean_active(u.get("auth_active_challenges"), now)
                    kept = [it for it in active if str(it.get("challenge_id") or "") != challenge_id]
                    user_ref.set({"auth_active_challenges": kept}, merge=True)
                except Exception:
                    # best-effort cleanup only
                    pass

        ch_ref.set({"consumed_at": now}, merge=True)

    # -------- Sessions --------
    def create_session(self, user_id: str, phone_e164: str, token: str, ttl_sec: int) -> Dict[str, Any]:
        now = int(time.time())
        token_hash = _sha256_hex(token)
        ref = self.db.collection(COL_AUTH_SESSIONS).document(token_hash)
        payload = {
            "user_id": user_id,
            "phone_e164": phone_e164,
            "token_hash": token_hash,
            "created_at": firestore.SERVER_TIMESTAMP,
            "expires_at": now + int(ttl_sec),
            "revoked_at": None,
        }
        ref.set(payload, merge=False)
        return {"session_id": token_hash, **payload}

    def get_session_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        token_hash = _sha256_hex(token)
        snap = self.db.collection(COL_AUTH_SESSIONS).document(token_hash).get()
        if not snap.exists:
            return None
        d = snap.to_dict() or {}
        d["session_id"] = token_hash
        return d

    def revoke_session(self, token: str) -> None:
        token_hash = _sha256_hex(token)
        self.db.collection(COL_AUTH_SESSIONS).document(token_hash).set(
            {"revoked_at": int(time.time())}, merge=True
        )

    # -------- Activation semantics --------
    def activate_user_if_needed(self, user_id: str, phone_e164: str) -> Dict[str, Any]:
        """
        OTP verification counts as activation.

        Sets users/{user_id}.phone and activated_at if missing.
        Always sets phone_verified_at for audit.
        Fail-closed: raises ValueError("user_not_found") if user doc missing.
        """
        now = int(time.time())
        user_ref = self.db.collection(COL_USERS).document(user_id)

        txn = self.db.transaction()

        @firestore.transactional
        def _run(tx: firestore.Transaction) -> Dict[str, Any]:
            snap = user_ref.get(transaction=tx)
            if not snap.exists:
                raise ValueError("user_not_found")
            u = snap.to_dict() or {}

            patch: Dict[str, Any] = {"phone_verified_at": now}
            did_set_phone = False
            did_set_activated = False

            if not u.get("phone"):
                patch["phone"] = phone_e164
                did_set_phone = True
            if not u.get("activated_at"):
                patch["activated_at"] = now
                did_set_activated = True

            tx.set(user_ref, patch, merge=True)
            return {"did_set_phone": did_set_phone, "did_set_activated_at": did_set_activated}

        return _run(txn)
