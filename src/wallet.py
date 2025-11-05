from dataclasses import dataclass
from base64 import b64encode
from pathlib import Path

from .install import Install, run_fift_script

_BOUNCEABLE_TAG = b"\x91"
_NON_BOUNCEABLE_TAG = b"\xd1"
_WORKCHAIN_REMAP = {
    b"\xff\xff\xff\xff": -1,
    b"\x00\x00\x00\x00": 0,
}


@dataclass
class TONAmount:
    nanoton: int

    def as_fift_argument(self):
        return f"{self.nanoton // 10**9}.{self.nanoton % 10**9:09}"


def ton(amount: str):
    nanoton = int(float(amount) * 10**9)
    assert nanoton >= 0
    return TONAmount(nanoton)


@dataclass
class SMCAddress:
    workchain: int
    address: bytes

    raw_address: str

    bounceable_address: str
    non_bounceable_address: str

    @staticmethod
    def from_parts(workchain: int, address: bytes):
        if len(address) != 32:
            raise ValueError("Raw address must be 32 bytes long")
        if workchain not in [-1, 0]:
            raise ValueError("Workchain must be -1 or 0")

        workchain_tag = b"\xff" if workchain == -1 else b"\x00"

        bounceable_addr = _BOUNCEABLE_TAG + workchain_tag + address
        non_bounceable_addr = _NON_BOUNCEABLE_TAG + workchain_tag + address

        def compute_crc(message: bytes):
            message += b"\x00\x00"
            poly = 0x1021
            reg = 0
            for byte in message:
                mask = 0x80
                while mask > 0:
                    reg <<= 1
                    if byte & mask:
                        reg += 1
                    mask >>= 1
                    if reg > 0xFFFF:
                        reg &= 0xFFFF
                        reg ^= poly
            return reg.to_bytes(2, "big")

        bounceable_addr = b64encode(
            bounceable_addr + compute_crc(bounceable_addr),
        ).decode("utf8")
        non_bounceable_addr = b64encode(
            non_bounceable_addr + compute_crc(non_bounceable_addr),
        ).decode("utf8")

        return SMCAddress(
            workchain=workchain,
            address=address,
            raw_address=f"{workchain}:{address.hex()}",
            bounceable_address=bounceable_addr,
            non_bounceable_address=non_bounceable_addr,
        )

    @property
    def non_bounceable(self):
        return TransactionDestination(self, False)

    @property
    def bounceable(self):
        return TransactionDestination(self, True)


@dataclass
class TransactionDestination:
    address: SMCAddress
    bounceable: bool

    def as_str(self):
        if self.bounceable:
            return self.address.bounceable_address
        else:
            return self.address.non_bounceable_address


@dataclass
class ExternalMessage:
    boc: bytes


def _add_suffix(path: Path, suffix: str) -> Path:
    return path.with_name(path.name + suffix)


@dataclass
class SimpleWallet:
    _install: Install
    address: SMCAddress
    path: Path
    seqno: int

    @staticmethod
    def from_path(install: Install, path: Path, seqno: int):
        with open(_add_suffix(path, ".addr"), "rb") as f:
            address = f.read(32)
            workchain = _WORKCHAIN_REMAP[f.read(4)]
        return SimpleWallet(install, SMCAddress.from_parts(workchain, address), path, seqno)

    @staticmethod
    def create(
        install: Install, path: Path, workchain: int
    ) -> tuple["SimpleWallet", ExternalMessage]:
        run_fift_script(
            install,
            install.script_new_wallet,
            [str(workchain), str(path)],
        )
        return (
            SimpleWallet.from_path(install, path, 0),
            ExternalMessage(_add_suffix(path, "-query.boc").read_bytes()),
        )

    def send(self, to: TransactionDestination, amount: TONAmount):
        run_fift_script(
            self._install,
            self._install.script_wallet,
            [
                str(self.path),
                to.as_str(),
                str(self.seqno),
                amount.as_fift_argument(),
                str(_add_suffix(self.path, "-tx")),
            ],
        )
        self.seqno += 1
        return ExternalMessage(_add_suffix(self.path, "-tx.boc").read_bytes())
