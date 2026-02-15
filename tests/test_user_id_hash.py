from utils.ids import user_id_from_phone_e164

def test_user_id_from_phone_e164():
    assert user_id_from_phone_e164("+15551234567").startswith("u_")
    assert len(user_id_from_phone_e164("+15551234567")) == 2 + 64
