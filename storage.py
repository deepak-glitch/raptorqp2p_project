import os, hashlib
from protocol import bdecode, bencode


class TorrentMeta:
    def __init__(self, torrent_file: str):
        bdata = bdecode(open(torrent_file,"rb").read())
        info = bencode(bdata[b"info"])
        self.info_hash = hashlib.sha1(info).digest()
        self.piece_length = bdata[b"info"][b"piece length"]
        self.piece_hashes = [
            bdata[b"info"][b"pieces"][i:i+20]
            for i in range(0, len(bdata[b"info"][b"pieces"]), 20)
        ]
        self.name = bdata[b"info"][b"name"].decode()

def read_symbol(download_dir, block_id, symbol_id, symbol_size):
    path = os.path.join(download_dir, f"{block_id}.blk")
    with open(path,"rb") as f:
        f.seek(symbol_id * symbol_size)
        return f.read(symbol_size)

def write_symbol(download_dir, block_id, symbol_id, data, total_symbols, symbol_size):
    os.makedirs(download_dir, exist_ok=True)
    path = os.path.join(download_dir, f"{block_id}.blk")
    mode = "r+b" if os.path.exists(path) else "wb"
    with open(path, mode) as f:
        f.seek(symbol_id * symbol_size)
        f.write(data)
