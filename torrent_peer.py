import socket, threading, time, random, os
import logging
from protocol import make_handshake, parse_handshake, unpack_message, msg_interested, msg_have, msg_symbol, unpack_symbol
from storage import TorrentMeta, write_block
from raptorqp2p import FileEncoder, FileDecoder, BlockDecoder, SymbolScheduler

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Peer:
    def __init__(self, mode, torrent_file, download_dir, peer_id, tracker_url):
        self.mode = mode            # '--seed' or '--leech'
        self.meta = TorrentMeta(torrent_file)
        self.download_dir = download_dir
        self.peer_id = peer_id.encode('latin-1')
        self.tracker = tracker_url
        self.encoder = FileEncoder(torrent_file)
        self.decoder = FileDecoder(None)
        self.block_decoders = {}
        self.scheduler = {}

    def announce(self):
        import requests
        params = {
            'info_hash': self.meta.info_hash.decode('latin-1'),
            'peer_id': self.peer_id.decode('latin-1'),
            'port': self.listen_port
        }
        requests.get(self.tracker + '/announce', params=params)

    def start(self):
        srv = socket.socket()
        srv.bind(('', 0))
        srv.listen(5)
        self.listen_port = srv.getsockname()[1]
        logging.info(f'Peer listening on {self.listen_port}')
        self.announce()

        conn, _ = srv.accept()
        self._setup_peer(conn)

    def _setup_peer(self, sock):
        sock.send(make_handshake(self.meta.info_hash, self.peer_id))
        sock.recv(68)
        sock.send(msg_interested())
        self.scheduler[sock] = SymbolScheduler(8, len(self.scheduler))
        threading.Thread(target=self._reader, args=(sock,), daemon=True).start()
        threading.Thread(target=self._writer, args=(sock,), daemon=True).start()

    def _reader(self, sock):
        while True:
            m = unpack_message(sock)
            if not m:
                break
            if m['id'] == 7:
                bid, sid, data = unpack_symbol(m['payload'])
                bd = self.block_decoders.setdefault(bid, BlockDecoder(None))
                bd.add_symbol(sid, data)
                self.scheduler[sock].update_received(bid, sid)
                if bd.complete:
                    blk = bd.decode()
                    write_block(self.download_dir, bid, blk)
                    self.decoder.add_block(bid, blk)
                    sock.send(msg_have(bid))
                    if self.decoder.complete:
                        full = self.decoder.decode()
                        os.makedirs(self.download_dir, exist_ok=True)
                        out_path = f"{self.download_dir}/{self.meta.name}"
                        with open(out_path, 'wb') as f:
                            f.write(full)
                        logging.info('File-level decode complete')
                        break

    def _writer(self, sock):
        if self.mode == '--seed':
            for bid in self.encoder.get_block_ids():
                syms = self.encoder.get_block_encoder(bid)
                for sid, dat in enumerate(syms):
                    sock.send(msg_symbol(bid, sid, dat))
                    time.sleep(0.005)
        else:
            # leecher does not push
            pass

if __name__ == '__main__':
    import sys
    mode = sys.argv[1]
    torrent = sys.argv[2]
    peer_id = '-' + str(random.randint(1000, 9999)) + '-P2P'
    tracker = 'http://localhost:8000'
    p = Peer(mode, torrent, 'downloads', peer_id, tracker)
    p.start()
    while True:
        time.sleep(1)