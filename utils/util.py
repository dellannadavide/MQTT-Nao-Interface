import utils.constants as Constants

import logging
logger = logging.getLogger("mqtt-nao-interface.utils.util")

def splitStringToList(str_to_split, separator=None):
    if separator is None:
        return str_to_split.split(Constants.STRING_SEPARATOR)
    else:
        return str_to_split.split(separator)

def joinStrings(list_to_join, separator=None):
    if separator is None:
        return Constants.STRING_SEPARATOR.join(list_to_join)
    else:
        return separator.join(list_to_join)
