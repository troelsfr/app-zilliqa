from ragger.backend import SpeculosBackend
from ragger.backend.interface import RaisePolicy
from ragger.bip import calculate_public_key_and_chaincode, CurveChoice

from ragger.navigator import NavInsID, NavIns

from apps.zilliqa import ZilliqaClient, ErrorType
from apps.txn_pb2 import ByteArray, ProtoTransactionCoreInfo

from utils import ROOT_SCREENSHOT_PATH, get_nano_review_instructions

ZILLIQA_KEY_INDEX = 1


def check_signature(client, backend, message, response):
    if isinstance(backend, SpeculosBackend):
        path = "44'/313'/{}'/0'/0'".format(ZILLIQA_KEY_INDEX)
        ref_public_key, _ = calculate_public_key_and_chaincode(CurveChoice.Secp256k1,
                                                               path,
                                                               compress_public_key=True)
        public_key = bytes.fromhex(ref_public_key)
    else:
        response = client.send_get_public_key_non_confirm(ZILLIQA_KEY_INDEX)
        public_key, address = client.parse_get_public_key_response(response.data)

    client.verify_signature(message, response, public_key)


def check_transaction(test_name, backend, navigator, transaction, instructions):
    client = ZilliqaClient(backend)
    with client.send_async_sign_transaction_message(ZILLIQA_KEY_INDEX, transaction):
        navigator.navigate_and_compare(ROOT_SCREENSHOT_PATH,
                                       test_name,
                                       instructions)
    response = client.get_async_response().data
    check_signature(client, backend, transaction, response)


def test_sign_tx_simple_accepted(test_name, firmware, backend, navigator):
    senderpubkey = ByteArray(data=bytes.fromhex("0205273e54f262f8717a687250591dcfb5755b8ce4e3bd340c7abefd0de1276574"))
    toaddr = bytes.fromhex("8AD0357EBB5515F694DE597EDA6F3F6BDBAD0FD9")
    amount = ByteArray(data=(100).to_bytes(16, byteorder='big'))
    gasprice = ByteArray(data=(1000000000).to_bytes(16, byteorder='big'))
    transaction = ProtoTransactionCoreInfo(
        version=65537,
        nonce=13,
        toaddr=toaddr,
        senderpubkey=senderpubkey,
        amount=amount,
        gasprice=gasprice,
        gaslimit=1
    ).SerializeToString()

    # Can't use navigate_until_text_and_compare because of the first screen and
    # approve screen both displaying "Sign" text.
    if firmware.device == "nanos":
        instructions = get_nano_review_instructions(6)
    else:
        instructions = get_nano_review_instructions(4)
    check_transaction(test_name, backend, navigator, transaction, instructions)


def test_sign_tx_simple_refused(test_name, firmware, backend, navigator):
    senderpubkey = ByteArray(data=bytes.fromhex("0205273e54f262f8717a687250591dcfb5755b8ce4e3bd340c7abefd0de1276574"))
    toaddr = bytes.fromhex("8AD0357EBB5515F694DE597EDA6F3F6BDBAD0FD9")
    amount = ByteArray(data=(100).to_bytes(16, byteorder='big'))
    gasprice = ByteArray(data=(1000000000).to_bytes(16, byteorder='big'))
    transaction = ProtoTransactionCoreInfo(
        version=65537,
        nonce=13,
        toaddr=toaddr,
        senderpubkey=senderpubkey,
        amount=amount,
        gasprice=gasprice,
        gaslimit=1
    ).SerializeToString()

    client = ZilliqaClient(backend)
    with client.send_async_sign_transaction_message(ZILLIQA_KEY_INDEX, transaction):
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        navigator.navigate_until_text_and_compare(NavIns(NavInsID.RIGHT_CLICK),
                                                  [NavIns(NavInsID.BOTH_CLICK)],
                                                  "Cancel",
                                                  ROOT_SCREENSHOT_PATH,
                                                  test_name)
    rapdu = client.get_async_response()
    assert rapdu.status == ErrorType.SW_USER_REJECTED
    assert len(rapdu.data) == 0


def test_sign_tx_data_accepted(test_name, firmware, backend, navigator):
    senderpubkey = ByteArray(data=bytes.fromhex("0205273e54f262f8717a687250591dcfb5755b8ce4e3bd340c7abefd0de1276574"))
    toaddr = bytes.fromhex("8AD0357EBB5515F694DE597EDA6F3F6BDBAD0FD9")
    amount = ByteArray(data=(100).to_bytes(16, byteorder='big'))
    gasprice = ByteArray(data=(1000000000).to_bytes(16, byteorder='big'))
    transaction = ProtoTransactionCoreInfo(
        version=65537,
        nonce=13,
        toaddr=toaddr,
        senderpubkey=senderpubkey,
        amount=amount,
        gasprice=gasprice,
        gaslimit=1,
        data=b"{'init':1}"
    ).SerializeToString()

    # Can't use navigate_until_text_and_compare because of the first screen and
    # approve screen both displaying "Sign" text.
    if firmware.device == "nanos":
        instructions = get_nano_review_instructions(7)
    else:
        instructions = get_nano_review_instructions(5)
    check_transaction(test_name, backend, navigator, transaction, instructions)


def test_sign_tx_code_accepted(test_name, firmware, backend, navigator):

    senderpubkey = ByteArray(data=bytes.fromhex("0205273e54f262f8717a687250591dcfb5755b8ce4e3bd340c7abefd0de1276574"))
    toaddr = bytes.fromhex("8AD0357EBB5515F694DE597EDA6F3F6BDBAD0FD9")
    amount = ByteArray(data=(100).to_bytes(16, byteorder='big'))
    gasprice = ByteArray(data=(1000000000).to_bytes(16, byteorder='big'))
    transaction = ProtoTransactionCoreInfo(
        version=65537,
        nonce=13,
        toaddr=toaddr,
        senderpubkey=senderpubkey,
        amount=amount,
        gasprice=gasprice,
        gaslimit=1,
        code=b" ".join([b"do stuff"] * 5)
    ).SerializeToString()

    # Can't use navigate_until_text_and_compare because of the first screen and
    # approve screen both displaying "Sign" text.
    if firmware.device == "nanos":
        instructions = get_nano_review_instructions(10)
    else:
        instructions = get_nano_review_instructions(6)
    check_transaction(test_name, backend, navigator, transaction, instructions)