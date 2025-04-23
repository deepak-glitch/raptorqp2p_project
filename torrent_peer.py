import socket, threading, time, random
from protocol import *
from storage import TorrentMeta, write_symbol
from raptorqp2p import FileEncoder, FileDecoder, BlockDecoder, SymbolScheduler
from utils import logging

MAX_INFLIGHT = 5
UNCHOKE_INTERVAL = 10

class Peer:
    def __init__(self, torrent_file, download_dir, peer_id, tracker_url,
                 block_size=1_600_000, symbol_size=16_000, repair_ratio=1.0, max_neighbors=8):
        self.meta = TorrentMeta(torrent_file)
        self.peer_id = peer_id
        self.download_dir = download_dir
        self.tracker = tracker_url
        self.block_size = block_size
        self.symbol_size = symbol_size
        self.encoder = FileEncoder(torrent_file, block_size, symbol_size, repair_ratio)
        self.decoder = FileDecoder(block_size)
        self.block_decoders = {}
        self.scheduler = {}
        self.max_neighbors = max_neighbors
        self.neighbors = []

    def announce(self):
        import requests
        params = {
            "info_hash": self.meta.info_hash.decode("latin-1"),
            "peer_id": self.peer_id,
            "port": self.listen_port
        }
        r = requests.get(self.tracker+"/announce", params=params)
        data = bdecode(r.content)
        peers = data[b"peers"]
        for i in range(0,len(peers),6):
            ip = ".".join(str(b) for b in peers[i:i+4])
            port = int.from_bytes(peers[i+4:i+6],"big")
            if (ip,port)!=(socket.gethostbyname(socket.gethostname()), self.listen_port):
                self.neighbors.append((ip,port))

    def start(self):
        srv = socket.socket(); srv.bind(("",0)); srv.listen(10)
        self.listen_port = srv.getsockname()[1]
        logging.info(f"Peer {self.peer_id} listening on {self.listen_port}")
        self.announce()
        def accept_loop():
            while True:
                c,_ = srv.accept()
                self._setup_peer(c)
        threading.Thread(target=accept_loop, daemon=True).start()
        for ip,port in random.sample(self.neighbors, min(len(self.neighbors), self.max_neighbors)):
            try:
                c=socket.socket(); c.connect((ip,port))
                self._setup_peer(c)
            except:
                continue
        threading.Thread(target=self._unchoke_loop, daemon=True).start()

    def _setup_peer(self, sock):
        sock.send(make_handshake(self.meta.info_hash, self.peer_id))
        resp = sock.recv(68)
        parse_handshake(resp)
        slot = len(self.scheduler)
        self.scheduler[sock] = SymbolScheduler(self.max_neighbors, slot)
        sock.send(msg_interested())
        threading.Thread(target=self._reader, args=(sock,), daemon=True).start()
        threading.Thread(target=self._writer, args=(sock,), daemon=True).start()

    def _reader(self, sock):
        inflight = {}
        while True:
            m = unpack_message(sock)
            if not m: break
            if m["id"]==7:
                bid, sid, data = unpack_symbol(m["payload"])
                if bid not in self.block_decoders:
                    self.block_decoders[bid] = BlockDecoder(self.symbol_size)
                bd = self.block_decoders[bid]
                bd.add_symbol(sid, data)
                self.scheduler[sock].update_received(bid, sid)
                write_symbol(self.download_dir, bid, sid, data, bd.decoder.source_block_count(), self.symbol_size)
                if bd.complete():
                    blk = bd.decode()
                    self.decoder.add_block(bid, blk)
                    sock.send(msg_have(bid))

    def _writer(self, sock):
        inflight = set()
        while True:
            for bid in range(self.encoder.total_blocks):
                if bid in inflight: continue
                slotSched = self.scheduler[sock]
                sid = slotSched.next_outgoing(bid)
                sock.send(msg_symbol(bid, sid, b""))
                inflight.add((bid,sid))
                if len(inflight)>=MAX_INFLIGHT:
                    break
            time.sleep(0.1)

    def _unchoke_loop(self):
        while True:
            for sock in list(self.scheduler):
                sock.send(msg_unchoke())
            time.sleep(UNCHOKE_INTERVAL)

if __name__=="__main__":
    import sys
    mode = sys.argv[1]
    target = sys.argv[2]
    peer_id = "-" + str(random.randint(1000,9999)) + "-" + "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(12))
    tracker = "http://localhost:8000"
    if mode=="--seed":
        p = Peer(target, "downloads", peer_id, tracker)
    else:
        p = Peer("my.torrent", "downloads", peer_id, tracker)
    p.start()
    while True:
        time.sleep(1)
