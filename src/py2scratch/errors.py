class PyToScratchError(Exception):
    """ A base error for the py2scratch project. """
class FuncNotFound(PyToScratchError):
    """ No FunctionDef is provided. """
class NoHatExists(PyToScratchError):
    """ There is no hat blocks with the specified name. """
class NoCostumeProvided(PyToScratchError):
    """ No costumes was added to the sprites/stage. """
class NonRootInlineBlocks(PyToScratchError):
    """Too many inline blocks. (Blocks with no `next` and `parent`)"""
class TypeUninferrable(PyToScratchError):
    """Cannot infer type of variable. Cannot statically compile function."""
class InvalidAudioFile(PyToScratchError):
    """ Invalid Audio File """

