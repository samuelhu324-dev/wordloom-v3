"""Block Exceptions"""
class BlockDomainException(Exception): pass
class BlockNotFoundError(BlockDomainException): pass
class InvalidBlockTypeError(BlockDomainException): pass
