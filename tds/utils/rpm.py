"""Classes for working with RPMs."""

import logging
import os.path
import subprocess

from . import run

log = logging.getLogger('tds.utils.rpm')


class RPMQueryProvider(object):
    """
    Provider for querying of data on an RPM file.
    """

    @classmethod
    def query(cls, filename, fields):
        """
        Query for given fields from file filename, assuming it's a valid RPM.
        """
        rpm_format = '\n'.join(
            ('%%{%s}' % field) for field in fields
        )

        try:
            rpm_query_result = run([
                'rpm', '-qp', '--queryformat',
                rpm_format,
                filename
            ])
        except subprocess.CalledProcessError as exc:
            log.error('rpm command failed: %s', exc)

            return None
        else:
            return zip(
                fields,
                rpm_query_result.stdout.splitlines()
            )


class RPMDescriptor(object):
    """
    Descriptor for an RPM.
    """

    query_fields = ('arch', 'name', 'version', 'release')
    arch = None
    name = None
    version = None
    release = None

    def __init__(self, path, **attrs):
        """
        Set up this descriptor for the given file path and attributes for the
        RPM.
        """
        self.path = path

        for key, val in attrs.items():
            setattr(self, key, val)

    @property
    def filename(self):
        """
        Return the filename of the RPM being described.
        If the full path to the file is "/opt/rpms/myrpm.rpm",
        then this will return "myrpm.rpm"
        """
        return os.path.basename(self.path)

    @property
    def package_info(self):
        """
        Return a select subset of the attributes of the RPM being described.
        """
        info = self.__dict__.copy()
        info.pop('path', None)
        info['revision'] = info.pop('release', None)

        return info

    @property
    def info(self):
        """
        Return info on the RPM being described.
        """
        #TODO We shouldn't be doing this dict pop trick.
        # Mike recommended possibly adding a hybrid property to the
        # tagopsdb.model.package.Package class.
        self_info = self.package_info
        self_info.pop('arch')
        return self_info

    @classmethod
    def from_path(cls, path):
        """
        Build a new RPM descriptor from the given path.
        """
        info = RPMQueryProvider.query(path, RPMDescriptor.query_fields)
        if info is None:
            return None
        return cls(path, **dict(info))
