# -*- coding: utf-8 -*-

from imio.pyutils.system import error
from imio.pyutils.system import read_csv
from imio.pyutils.system import verbose

import argparse
import os
import sys


def compare_tree_files():
    """Compares a tree file with a reference tree file"""
    parser = argparse.ArgumentParser(description='Compare a tree file with a reference one')
    parser.add_argument('-r', '--reference', dest='ref_file', help='Reference file (csv format)', required=True)
    parser.add_argument('-rc', '--reference_config', dest='ref_conf', required=True,
                        help='Reference file configuration: "skip lines|separator|id col|title col" (starting at 0)')
    parser.add_argument('-f', '--file', dest='tree_file', help='Tree file (csv format)', required=True)
    parser.add_argument('-fc', '--file_config', dest='file_conf', required=True,
                        help='Tree file configuration: "skip lines|separator|id col|title col" (starting at 0)')
    ns = parser.parse_args()
    verbose("Start of %s" % sys.argv[0])
    ref_confs = ns.ref_conf.split('|')
    if len(ref_confs) != 4:
        error("rc parameter not well formated: {}".format(ns.ref_conf))
        sys.exit(1)
    skip_lines, ref_sep, ref_id_col, ref_tit_col = int(ref_confs[0]), ref_confs[1], int(ref_confs[2]), int(ref_confs[3])
    lines = read_csv(ns.ref_file, skip_lines=skip_lines, delimiter=ref_sep)
    ref_dic = {}
    for line in lines:
        k = line[ref_id_col]
        if k in ref_dic:
            error("Ref id already exists: {} : {} <=> {}".format(k, ref_dic[k], line[ref_tit_col]))
        else:
            ref_dic[k] = line[ref_tit_col]
    verbose("End of %s" % sys.argv[0])
