import grp
import os
import pwd
import re
from datetime import datetime

proj_home = os.path.realpath(os.path.dirname(__file__)+ "/../")

class BackupFileException(Exception):
    pass

class FileOwnershipException(Exception):
    pass

class MatchFormatException(Exception):
    pass

class MissingFileException(Exception):
    pass

class UserSubmittedException(Exception):
    pass

# file handling routines
def chowner(filename, uname="ads", ugroup="ads"):
    try:
        uid = pwd.getpwnam(uname).pw_uid
        gid = grp.getgrnam(ugroup).gr_gid
        os.chown(filename, uid, gid)
    except Exception as err:
        raise FileOwnershipException(err)

def backup_to_frozen(live_file, frozen_file):
    if (os.path.isfile(live_file)) and (os.path.isfile(frozen_file)):
        timestamp = str(datetime.now())
        separator = "#\n# %s\n#" % timestamp
        blank_header = "# User submitted preprint links, one per line, tab-separated values:\n# preprint bibcode\tpublished bibcode"
        try:
            data = []
            with open(live_file, "r") as fl:
                for line in fl.readlines():
                    data.append(line)
            outdata = "".join(data)
            os.chmod(frozen_file, 0o666)
            with open(frozen_file, "a") as fo:
                fo.write("%s\n" % separator)
                fo.write("%s\n" % outdata)
            os.chmod(frozen_file, 0o444)
            chowner(frozen_file)
            with open(live_file, "w") as fl:
                fl.write("%s\n" % blank_header)
            chowner(live_file)
        except Exception as err:
            raise BackupFileException(err)

    else:
        raise MissingFileException("One or both of %s, %s are missing." % live_file, frozen_file)

# processing routines
def dedup_pairs(input_pairs):
    if input_pairs:
        try:
            output_pairs = []
            output_resolve = []
            for (pre, pub) in input_pairs:
                pre_list = [x for (x,y) in output_pairs]
                pub_list = [y for (x,y) in output_pairs]
                if (pre, pub) not in output_pairs:
                    if pre not in pre_list and pub not in pub_list and \
                        pre not in pub_list and pub not in pre_list:
                        output_pairs.append((pre, pub))
                    else:
                        output_resolve.append((pre, pub))
            return output_pairs, output_resolve
        except Exception as err:
            raise MatchFormatException(err)
    return [], []



def read_user_submitted(input_filename):
    try:
        input_pairs=[]
        failed_lines=[]
        with open(input_filename, "r") as fc:
            for line in fc.readlines():
                if not re.search(r"^\s?#", line):
                    try:
                        (pre, pub) = line.strip().split('\t')
                    except:
                        failed_lines.append(line)
                    else:
                        input_pairs.append((pre,pub))
        return input_pairs, failed_lines
    except Exception as err:
        raise UserSubmittedException(err)
