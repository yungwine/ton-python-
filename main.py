import asyncio
import logging
from pathlib import Path
import shutil

from src.install import Install
from src.network import Network
from src.wallet import ton


async def main() -> None:
    working_dir = Path(".network")
    shutil.rmtree(working_dir, ignore_errors=True)
    working_dir.mkdir(exist_ok=True)

    install = Install(
        Path("/home/danklishch/code/ton/src/build"),
        Path("/home/danklishch/code/ton/src"),
    )

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s][%(asctime)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H-%M-%S",
    )

    async with Network(install, working_dir) as network:
        dht = network.create_dht_node()

        node = network.create_full_node()
        node.make_initial_validator()
        node.announce_to(dht)

        await dht.run()
        await node.run()

        await network.wait_mc_block(seqno=1)

        wallet, wallet_init = network.create_wallet(0)
        tx = network.zerostate.main_wallet.send(wallet.address.non_bounceable, ton("2"))
        await network.send_external_message(tx)
        await asyncio.sleep(30)
        await network.send_external_message(wallet_init)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
