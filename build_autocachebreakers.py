#!/usr/bin/env python

from hashlib import md5
from StringIO import StringIO

try:
	from twisted.python.filepath import FilePath
except ImportError:
	from filepath import FilePath


def _getLocals(fname):
	lokals = {}
	execfile(fname, {}, lokals)
	return lokals


def _makeGeneratedFileContent(target):
	s = StringIO()
	s.write("""\
/**
 * DO NOT EDIT.  This file was generated by build_cachebreakers.py,
 * which read a targets_cb.py file for instructions.
 */

""")
	for propertyName, _ in target["breakers"]:
		s.write("""\
goog.provide('%s');
""" % (propertyName,))

	s.write('\n')

	for propertyName, fname in target["breakers"]:
		digest = md5(FilePath(fname).getContent()).hexdigest()
		s.write("""\
%s = '%s';
""" % (propertyName, digest))

	return s.getvalue()


def writeFiles(targets):
	for target in targets:
		out = FilePath(target["output"])
		newContent = _makeGeneratedFileContent(target)

		# Check if the file needs to be updated.  Avoid writing if it's
		# identical, to avoid triggering automatic rebuilds of compiled
		# JavaScript.
		try:
			oldContent = out.getContent()
		except IOError:
			oldContent = None

		if newContent != oldContent:
			out.setContent(newContent)


def main():
	targets = _getLocals("targets_cb.py")["targets"]
	writeFiles(targets)


if __name__ == '__main__':
	main()
