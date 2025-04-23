import struct
import bencodepy

# ——— BitTorrent handshake & messages ———
BT_PROTOCOL = b"BitTorrent protocol"

def make_handshake(info_hash: bytes, peer_id: bytes) -> bytes:
    return (
        struct.pack(">B", len(BT_PROTOCOL))
        + BT_PROTOCOL
        + b'\x00'*8
        + info_hash
        + peer_id
    )

def parse_handshake(data: bytes):
    pstrlen = data[0]
    assert data[1:1+pstrlen] == BT_PROTOCOL
    return {
        "info_hash": data[1+pstrlen+8:1+pstrlen+8+20],
        "peer_id": data[-20:],
    }

def pack_message(msg_id: int, payload: bytes = b"") -> bytes:
    length = 1 + len(payload)
    return struct.pack(">I", length) + struct.pack(">B", msg_id) + payload

def unpack_message(sock):
    header = sock.recv(4)
    if not header: return None
    length = struct.unpack(">I", header)[0]
    if length == 0:
        return {"id": None, "payload": b""}
    body = sock.recv(length)
    return {"id": body[0], "payload": body[1:]}

# standard BT messages (ID)
def msg_choke():        return pack_message(0)
def msg_unchoke():      return pack_message(1)
def msg_interested():   return pack_message(2)
def msg_not_interested(): return pack_message(3)
def msg_have(idx: int): return pack_message(4, struct.pack(">I", idx))
def msg_bitfield(bf: bytes): return pack_message(5, bf)
def msg_request(idx, begin, length):
    return pack_message(6, struct.pack(">III", idx, begin, length))
def msg_piece(idx, begin, block):
    return pack_message(7, struct.pack(">II", idx, begin) + block)

# extended for RaptorQ: reuse ID=7 but payload = block_id(4)|symbol_id(4)|data
def msg_symbol(block_id: int, symbol_id: int, data: bytes):
    return pack_message(7, struct.pack(">II", block_id, symbol_id) + data)

def unpack_symbol(payload: bytes):
    block_id, symbol_id = struct.unpack(">II", payload[:8])
    return block_id, symbol_id, payload[8:]

# bencode helpers
bencode = bencodepy.encode
bdecode = bencodepy.decode
