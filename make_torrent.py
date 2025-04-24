# make_torrent.py
import os, hashlib
import bencodepy

def make_torrent(filename, announce, piece_length, output):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found in {os.getcwd()}")
    size = os.path.getsize(filename)

    # build the 'pieces' string by SHA-1 hashing each piece
    pieces = b""
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(piece_length)
            if not chunk:
                break
            pieces += hashlib.sha1(chunk).digest()

    info = {
        b"name": os.path.basename(filename).encode(),
        b"piece length": piece_length,
        b"length": size,
        b"pieces": pieces
    }
    metadata = {
        b"announce": announce.encode(),
        b"info": info
    }

    with open(output, "wb") as out:
        out.write(bencodepy.encode(metadata))
    print(f"Created torrent file: {output}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Make a .torrent file")
    p.add_argument("file", help="File to distribute (e.g. RaptorQP2P.pdf)")
    p.add_argument("-a","--announce", default="http://localhost:8000/announce",
                   help="Tracker announce URL")
    p.add_argument("-l","--piece-length", type=int, default=2**20,
                   help="Piece length in bytes (default 1 MiB)")
    p.add_argument("-o","--output", default="out.torrent",
                   help="Output .torrent filename")
    args = p.parse_args()
    make_torrent(args.file, args.announce, args.piece_length, args.output)
