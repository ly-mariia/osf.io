from boto.exception import *
from boto.s3.connection import *
from boto.s3.cors import CORSConfiguration

from hurry.filesize import size, alternative

import os
import re
from boto.iam import *
import json
from datetime import datetime


def has_access(access_key, secret_key):
    try:
        c = S3Connection(access_key, secret_key)
        c.get_all_buckets()
        return True
    except Exception:
        return False


def get_bucket_list(user_settings):
        return S3Connection(user_settings.access_key, user_settings.secret_key).get_all_buckets()


def create_bucket(user_settings, bucket_name):
    try:
        connect = S3Connection(
            user_settings.access_key, user_settings.secret_key)
        return connect.create_bucket(bucket_name)
    except Exception:
        return False


def create_limited_user(accessKey, secretKey, bucketName, pid):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt1390848602000",
                "Effect": "Deny",
                "Action": [
                    "s3:DeleteBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::{bucketname}".format(bucketname=bucketName)
                ]
            },
            {
                "Sid": "Stmt1390848639000",
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    "arn:aws:s3:::{bucketname}".format(
                        bucketname=bucketName),
                    "arn:aws:s3:::{bucketname}/*".format(
                        bucketname=bucketName)
                ]
            }
        ]
    }
    connection = IAMConnection(accessKey, secretKey)
    connection.create_user(bucketName + '-osf-limited-' + pid)
    # This might need a bit more try catching
    connection.put_user_policy(
        bucketName + '-osf-limited-' + pid, 'policy-' + bucketName + '-osf-limited-' + pid, json.dumps(policy))
    return connection.create_access_key(bucketName + '-osf-limited-' + pid)['create_access_key_response']['create_access_key_result']['access_key']

# TODO Add PID


def remove_user(accessKey, secretKey, bucketName, otherKey, pid):
    connection = IAMConnection(accessKey, secretKey)
    connection.delete_user_policy(
        bucketName + '-osf-limited-' + pid, 'policy-' + bucketName + '-osf-limited-' + pid)
        # bucketName + '-osf-limited', 'policy-' + bucketName + '-osf-limited-'
        # + pid)
    connection.delete_access_key(otherKey, bucketName + '-osf-limited-' + pid)
    connection.delete_user(bucketName + '-osf-limited-' + pid)


def does_bucket_exist(accessKey, secretKey, bucketName):
    try:
        c = S3Connection(accessKey, secretKey)
        c.get_bucket(bucketName)
        return True
    except Exception:
        return False


class S3Wrapper:

    @classmethod
    def from_addon(cls, s3):
        if not s3.is_registration:
            return cls(S3Connection(s3.node_access_key, s3.node_secret_key), s3.bucket)
        else:
            return registration_wrapper(s3)

    @classmethod
    def from_user(cls, s3, bucket):
        return cls(S3Connection(s3.access_key, s3.secret_key), bucket)

    @classmethod
    def bucket_exist(cls, s3, bucketName):
        m = cls.fromAddon(s3)
        try:
            m.connection.get_bucket(bucketName.lower())
            return True
        except Exception:
            return False

    "S3 Bucket management"

    def __init__(self, connect, bucketName):
        self.connection = connect
        self.bucket = self.connection.get_bucket(bucketName)

    def create_key(self, key):
        self.bucket.new_key(key)

    def post_string(self, title, contentspathToFolder=""):
        k = self.bucket.new_key(pathToFolder + title)
        return k.set_contents_from_string(contents)

    def get_string(self, title):
        return self.bucket.get_key(title).get_contents_as_string()

    def set_metadata(self, bucket, key, metadataName, metadata):
        k = self.connection.get_bucket(bucket).get_key(key)
        return k.set_metadata(metadataName, metadata)

    def get_file_list(self, prefix=None):
        if not prefix:
            return self.bucket.list()
        else:
            return self.bucket.list(prefix=prefix)

    def create_folder(self, name, pathToFolder=""):
        if not name.endswith('/'):
            name.append("/")
        k = self.bucket.new_key(pathToFolder + name)
        return k.set_contents_from_string("")

    def delete_file(self, keyName):
        return self.bucket.delete_key(keyName)

    # TODO Test me I might not work
    def get_MD5(self, keyName):
        '''returns the MD5 hash of a file.

        params str keyName: The name of the key to hash

        '''
        return self.bucket.get_key(keyName).get_md5_from_hexdigest()

    def download_file_URL(self, keyName, vid=None):
        return self.bucket.get_key(keyName, version_id=vid).generate_url(5)

    def get_wrapped_keys(self, prefix=None):
        return [S3Key(x) for x in self.get_file_list()]

    def get_wrapped_key(self, keyName, vid=None):
        return S3Key(self.bucket.get_key(keyName, version_id=vid))

    def get_wrapped_keys_in_dir(self, directory=None):
        return [S3Key(x) for x in self.bucket.list(delimiter='/', prefix=directory) if isinstance(x, Key) and x.key != directory]

    def get_wrapped_directories_in_dir(self, directory=None):
        return [S3Key(x) for x in self.bucket.list(prefix=directory) if isinstance(x, Key) and x.key.endswith('/') and x.key != directory]

    @property
    def bucket_name(self):
        return self.bucket.name

    def get_version_data(self):
        versions = {}
        versions_list = self.bucket.list_versions()
        for p in versions_list:
            if isinstance(p, Key) and str(p.version_id) != 'null' and str(p.key) not in versions:
                versions[str(p.key)] = [str(k.version_id)
                                        for k in versions_list if p.key == k.key]
        return versions
        # TODO update this to cache results later

    def get_file_versions(self, file_name):
        return [x for x in self.bucket.list_versions(prefix=file_name) if isinstance(x, Key)]

    def get_cors_rules(self):
        try:
            return self.bucket.get_cors()
        except:
            return CORSConfiguration()

    def set_cors_rules(self, rules):
        return self.bucket.set_cors(rules)


class registration_wrapper(S3Wrapper):

    def __init__(self, node_settings):
        S3Wrapper.__init__(self,
            S3Connection(node_settings.node_access_key, node_settings.node_secret_key), node_settings.bucket)
        self.registration_data = node_settings.registration_data

    def get_wrapped_keys_in_dir(self, directory=None):
        #assert 0, self.registration_data
        return [S3Key(x) for x in self.bucket.list_versions(delimiter='/', prefix=directory) if isinstance(x, Key) and x.key != directory and self.is_right_version(x)]

    def get_wrapped_directories_in_dir(self, directory=None):
        return [S3Key(x) for x in self.bucket.list_versions(prefix=directory) if isinstance(x, Key) and x.key.endswith('/') and x.key != directory and self.is_right_version(x)]

    def is_right_version(self, key):
        return [x for x in self.registration_data['keys'] if x['version_id'] == key.version_id]



# TODO Extend me and you bucket.setkeyclass
class S3Key:

    def __init__(self, key):
        self.s3Key = key
        if self.type == 'file':
            self.versions = ['current']
        else:
            self.version = None

    @property
    def name(self):
        d = self._nameAsStr().split('/')
        if len(d) > 1 and self.type == 'file':
            return d[-1]
        elif self.type == 'folder':
            return d[-2]
        else:
            return d[0]

    def _nameAsStr(self):
        return str(self.s3Key.key)

    @property
    def type(self):
        if not str(self.s3Key.key).endswith('/'):
            return 'file'
        else:
            return 'folder'

    @property
    def fullPath(self):
        return self._nameAsStr()

    @property
    def parentFolder(self):
        d = self._nameAsStr().split('/')

        if len(d) > 1 and self.type == 'file':
            return d[len(d) - 2]
        elif len(d) > 2 and self.type == 'folder':
            return d[len(d) - 3]
        else:
            return None

    @property
    def pathTo(self):
        return self._nameAsStr()[:self._nameAsStr().rfind('/')] + '/'

    @property
    def size(self):
        if self.type == 'folder':
            return None
        else:
            return size(float(self.s3Key.size), system=alternative)

    @property
    def lastMod(self):
        if self.type == 'folder':
            return None
        else:
            m = re.search(
                '(.+?)-(.+?)-(\d*)T(\d*):(\d*):(\d*)', str(self.s3Key.last_modified))
            if m is not None:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
            else:
                return None

    @property
    def version(self):
        return self.versions

    @property
    def extension(self):
        if self.type != 'folder':
            if os.path.splitext(self._nameAsStr())[1] is None:
                return None
            else:
                return os.path.splitext(self._nameAsStr())[1][1:]
        else:
            return None

    @property
    def md5(self):
        return self.s3Key.md5

    @property
    def version_id(self):
        return self.s3Key.version_id if self.s3Key.version_id != 'null' else 'Current'

    def updateVersions(self, manager):
        if self.type != 'folder':
            self.versions.extend(manager.get_file_versions(self._nameAsStr()))
