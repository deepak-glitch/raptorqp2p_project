from raptorq import Encoder as RQEncoder, Decoder as RQDecoder

class FileEncoder:
    def __init__(self, file_path, block_size=1_600_000, symbol_size=16_000, repair_ratio=1.0):
        data = open(file_path,"rb").read()
        self.block_size = block_size
        self.symbol_size = symbol_size
        self.fenc = RQEncoder(data, block_size)
        self.S = self.fenc.source_block_count()
        self.R = int(self.S * repair_ratio)
        self.total_blocks = self.S + self.R
        self.block_encoders = {}

    def get_block_ids(self):
        return list(range(self.total_blocks))

    def get_block(self, block_id):
        return self.fenc.get_symbol(block_id)

    def get_block_encoder(self, block_id):
        if block_id not in self.block_encoders:
            blk = self.get_block(block_id)
            self.block_encoders[block_id] = RQEncoder(blk, self.symbol_size)
        return self.block_encoders[block_id]

class FileDecoder:
    def __init__(self, block_size=1_600_000):
        self.decoder = RQDecoder(block_size)

    def add_block(self, block_id, data):
        self.decoder.add_symbol(block_id, data)

    def complete(self):
        return self.decoder.is_complete()

    def decode(self):
        return self.decoder.decode()

class BlockDecoder:
    def __init__(self, symbol_size):
        self.decoder = RQDecoder(symbol_size)

    def add_symbol(self, symbol_id, data):
        self.decoder.add_symbol(symbol_id, data)

    def complete(self):
        return self.decoder.is_complete()

    def decode(self):
        return self.decoder.decode()

class SymbolScheduler:
    def __init__(self, total_slots, slot_index):
        self.N = total_slots
        self.slot = slot_index
        self.max_symbol = {}

    def next_outgoing(self, block_id):
        ms = self.max_symbol.get(block_id, -1) + 1
        while ms % self.N != self.slot:
            ms += 1
        self.max_symbol[block_id] = ms
        return ms

    def update_received(self, block_id, symbol_id):
        cur = self.max_symbol.get(block_id, -1)
        if symbol_id > cur:
            self.max_symbol[block_id] = symbol_id
