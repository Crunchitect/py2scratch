class PyToScratchError(Exception):
    """ A base error for the py2scratch project. """
class FuncNotFound(PyToScratchError):
    """ No FunctionDef is provided. """
class NoHatExists(PyToScratchError):
    """ There is no hat blocks with the specified name. """
class NoCostumeProvided(PyToScratchError):
    """ No costumes was added to the sprites/stage. """
class InvalidAudioFile(PyToScratchError):
    """ Invalid Audio File """

