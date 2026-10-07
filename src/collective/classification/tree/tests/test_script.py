# -*- coding: utf-8 -*-
"""Console scripts tree_compare_files, tree_add_parent and tree_add_archived"""

from collective.classification.tree import script
from io import StringIO

import io
import os
import shutil
import sys
import tempfile
import unittest


class TestScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _csv(self, name, lines):
        path = os.path.join(self.tmp, name)
        with io.open(path, "w", encoding="utf8") as f:
            f.write("\n".join(lines) + "\n")
        return path

    def _run(self, function, *args):
        """Run the console script with these command line arguments, return its output"""
        argv, stdout = sys.argv, sys.stdout
        sys.argv, sys.stdout = [function.__name__] + list(args), StringIO()
        try:
            function()
            return sys.stdout.getvalue()
        finally:
            sys.argv, sys.stdout = argv, stdout

    def _read(self, path):
        with io.open(path, encoding="utf8") as f:
            return f.read().splitlines()

    def test_compare_tree_files(self):
        ref = self._csv("ref.csv", ["-1;Administration", "-1.1;Personnel"])
        tree = self._csv("tree.csv", ["1;Administration", "1.1;Staff", "9;Unknown"])
        output = self._run(
            script.compare_tree_files,
            "-r",
            ref,
            "-rc",
            "0|;|0|1",
            "-f",
            tree,
            "-fc",
            "0|;|0|1",
        )
        self.assertIn(
            "2,0, id '-1.1', different titles: 'Staff' <=> 'Personnel'", output
        )
        self.assertIn("3,0, id '9', not found in ref (tit='Unknown')", output)
        self.assertNotIn("id '-1',", output)

    def test_add_parent(self):
        tree = self._csv(
            "tree.csv", ["Code;Title", "1;Administration", "1.1;Personnel"]
        )
        self._run(script.add_parent, tree, "-c", ";|0||")
        self.assertEqual(
            [
                '"Code";"Title";"Parent"',
                '"1";"Administration";""',
                '"1.1";"Personnel";"1"',
            ],
            self._read(os.path.join(self.tmp, "tree_parent.csv")),
        )

    def test_add_archived(self):
        tree = self._csv(
            "tree.csv",
            [
                "Code;Title;Archived;SubId;SubTitle",
                "1;Folder;VRAI;;",
                "1.1;Folder;0;5;Sub",
            ],
        )
        self._run(script.add_archived, tree, "-c", ";|2|3|4")
        self.assertEqual(
            [
                '"Code";"Title";"Archived";"SubId";"SubTitle";"Archivé farde";"Archivé chemise"',
                '"1";"Folder";"VRAI";"";"";"1";""',  # archived value kept as is
                '"1.1";"Folder";"0";"5";"Sub";"";""',
            ],
            self._read(os.path.join(self.tmp, "tree_archived.csv")),
        )
