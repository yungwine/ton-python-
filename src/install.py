from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


@dataclass
class Install:
    build_dir: Path
    source_dir: Path

    @property
    def fift_create_state_exe(self):
        return self.build_dir / "crypto/create-state"

    @property
    def fift_exe(self):
        return self.build_dir / "crypto/fift"

    @property
    def fift_include_dirs(self):
        return [
            self.source_dir / "crypto/fift/lib",
            self.source_dir / "crypto/smartcont",
        ]

    @property
    def key_helper_exe(self):
        return self.build_dir / "utils/generate-random-id"

    @property
    def validator_engine_exe(self):
        return self.build_dir / "validator-engine/validator-engine"

    @property
    def dht_server_exe(self):
        return self.build_dir / "dht-server/dht-server"

    @property
    def tonlibjson(self):
        return self.build_dir / "tonlib/libtonlibjson.so"

    @property
    def script_new_wallet(self):
        return self.source_dir / "crypto/smartcont/new-wallet.fif"

    @property
    def script_wallet(self):
        return self.source_dir / "crypto/smartcont/wallet.fif"


def run_fift_create_state(install: Install, code: str, working_dir: Path):
    script_file = working_dir / "script.fif"
    _ = script_file.write_text(code)

    args = [install.fift_create_state_exe]
    for include_dir in install.fift_include_dirs:
        args += ["-I", include_dir]
    args += ["-s", "script.fif"]

    _ = subprocess.run(args, cwd=working_dir, check=True)

    os.remove(script_file)


def run_fift_script(
    install: Install,
    script: Path,
    arguments: list[str],
    working_dir: Path | None = None,
):
    args = [install.fift_exe]
    for include_dir in install.fift_include_dirs:
        args += ["-I", include_dir]
    args += ["-s", script]
    args += arguments

    _ = subprocess.run(args, cwd=working_dir, check=True)
