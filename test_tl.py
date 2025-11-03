from tl.tl_gen.lite_api.types.tonNode import BlockIdExt
from tl.tl_gen.ton_api.types.pk import Aes
from tl.tl_gen.ton_api.types.pub import Unenc
from tl.tl_gen.ton_api.types.id import ConfigLocal
from tl.tl_gen.ton_api.types.catchain import ConfigGlobal



block = BlockIdExt(workchain=-1, shard=0, seqno=123456, root_hash=321, file_hash=456)

print(block)
print(block.to_dict())
block2 = BlockIdExt.from_dict(block.to_dict())

assert block == block2

pk = Aes(key=int.from_bytes(b'\x01'*32, 'big'))

c = ConfigLocal(id=pk)
print(c)
print(c.to_dict())
c2 = ConfigLocal.from_dict({'_': 'ConfigLocal', 'id': {'_': 'Aes', 'key': 454086624460063511464984254936031011189294057512315937409637584344757371137}})
print(c2)

assert c == c2

pubk = Unenc(data=b'\x12'*32)


cg = ConfigGlobal(tag=123, nodes=[pubk, pubk])
print(cg)
print(cg.to_dict())
cg2 = ConfigGlobal.from_dict(cg.to_dict())
print(cg2)

assert cg == cg2


from tl.tl_gen.lite_api.functions.liteServer import GetBlockHeaderRequest

req = GetBlockHeaderRequest(id=block, mode=2)
print(req)
print(req.to_dict())
req2 = GetBlockHeaderRequest.from_dict(req.to_dict())
print(req2)
assert req == req2


from tl.tl_gen.ton_api.types.adnl import PacketContents

pc = PacketContents(rand1=b'\x01\x01', flags=1, rand2=b'\x01\x01', from_=pubk)
print(pc)
print(pc.to_dict())
pc2 = PacketContents.from_dict(pc.to_dict())
print(pc2)
assert pc == pc2

from tl.binary_reader import BinaryReader
from tl.tl_gen.lite_api.alltlobjects import tlobjects
reader = BinaryReader(block.to_bytes()[4:], tl_objects=tlobjects)  # skip tag
blk2 = BlockIdExt.from_reader(reader)
print(blk2, block)
assert blk2 == block
