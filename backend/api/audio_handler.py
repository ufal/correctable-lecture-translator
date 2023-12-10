from typing import List

class AudioBuffer:
    def __init__(self, SNIPPET_SIZE: int, SHIFT_LENGTH: int):
        # config
        self.SNIPPET_SIZE = SNIPPET_SIZE
        self.SHIFT_LENGTH = SHIFT_LENGTH

        # data
        self.buffer: List[bytes] = []
        self.smallest_available_timestamp = 0

    def extend(self, chunk):
        self.buffer.extend(chunk)

    def get_snippet(self, timestamp: int) -> List[bytes]:
        actuall_timestamp = timestamp - self.smallest_available_timestamp
        return self.buffer[
            actuall_timestamp * self.SHIFT_LENGTH : actuall_timestamp * self.SHIFT_LENGTH
            + self.SNIPPET_SIZE
        ]

    def can_get_snippet(self, timestamp: int):
        actuall_timestamp = timestamp - self.smallest_available_timestamp
        return actuall_timestamp * self.SHIFT_LENGTH + self.SNIPPET_SIZE <= len(self.buffer)

    def shift(self):
        if len(self.buffer) > self.SNIPPET_SIZE:
            self.smallest_available_timestamp += 1
            self.buffer = self.buffer[self.SHIFT_LENGTH :]

    def clear(self):
        self.buffer = []
        self.smallest_available_timestamp = 0

    def __len__(self):
        return len(self.buffer)
