
import urllib.parse
import pathlib

import logging
logger= logging.getLogger("editing.fileops")


# Developer Note: These implementation use the PurePath
# classes from the standard pathlib module. This will make
# it possible to test these function on 'foreign' systems, for 
# example we can check the results of the functions in a Mac/Linux 
# execution but pass the PureWindowsPath class in to the functions

def path_to_uri(filepath : str , path_class = pathlib.PurePath ) -> str:
    """
    returns a file schema URI from a filesystem absolute path
    """
    return path_class(filepath).as_uri()

# the code in uri_to_path was submitted by user Iwan Aucamp: 
# https://stackoverflow.com/users/1598080/iwan-aucamp
# as an answer to question is-there-a-convenient-way-to-map-a-file-uri-to-os-path
# https://stackoverflow.com/questions/5977576/is-there-a-convenient-way-to-map-a-file-uri-to-os-path
#
# licensed under https://opensource.org/licenses/0BSD  Aug 2019

# has also been modified to take advantage of a direct implementation of this
# functionality available in the standard pathlib module at version 3.13
# Blender 4.5 is using Python 3.11


def uri_to_path(file_uri : str, path_class = pathlib.PurePath ) -> str:
    """
    This function returns a pathlib.PurePath object for the supplied file URI.

    :param str file_uri: The file URI ...
    :param class path_class: The type of path in the file_uri. By default it uses
        the system specific path pathlib.PurePath, to force a specific type of path
        pass pathlib.PureWindowsPath or pathlib.PurePosixPath
    :returns: the pathlib.PurePath object
    :rtype: pathlib.PurePath
    """
    import sys
    if sys.version_info.major == 3 and sys.version_info.minor >= 13:
        logger.debug("using pathlib for uri_to_path")
        return path_class().from_uri(file_uri) # pyright: ignore
    else:        
        logger.debug("using 3rd party solution for uri_to_path")        
        windows_path = isinstance(path_class(),pathlib.PureWindowsPath)
        file_uri_parsed = urllib.parse.urlparse(file_uri)
        file_uri_path_unquoted = urllib.parse.unquote(file_uri_parsed.path)
        if windows_path and file_uri_path_unquoted.startswith("/"):
            result = path_class(file_uri_path_unquoted[1:])
        else:
            result = path_class(file_uri_path_unquoted)
        if not result.is_absolute() :
            raise ValueError("Invalid file uri {} : resulting path {} not absolute".format(
                file_uri, result))
        return str(result)
        
def uri_scheme(uri:str) -> str:
    """
    returns string value such as http, https, file
    """
    return urllib.parse.urlparse(uri).scheme 