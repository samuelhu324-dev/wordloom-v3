"""Media Exceptions"""
class MediaDomainException(Exception): pass
class MediaNotFoundError(MediaDomainException): pass
class DuplicateMediaError(MediaDomainException): pass
