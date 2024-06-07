# -*- coding: utf-8 -*-

from collections import OrderedDict
from collective.classification.tree.utils import get_decimal_parent
from collective.classification.tree.utils import get_parents
from imio.pyutils.system import error
from imio.pyutils.system import read_csv
from imio.pyutils.system import verbose

import argparse
import csv
import re
import sys

decimal_identifier = r"-?[.\d]+$"


def compare_tree_files():
    """Compares a tree file with a reference tree file"""
    parser = argparse.ArgumentParser(description="Compare a tree file with a reference one")
    parser.add_argument(
        "-p", "--parts", dest="parts", help="Run parts: 1 (load ref), 2 (load tree), 3 (compare)", default="123"
    )
    parser.add_argument("-r", "--reference", dest="ref_file", help="Reference file (csv format)")
    parser.add_argument(
        "-rc",
        "--reference_config",
        dest="ref_conf",
        help='Reference file configuration: "skip lines|separator|id col|title col" (starting at 0). ' "Like: 1|;|0|1",
    )
    parser.add_argument("-f", "--file", dest="tree_file", help="Tree file (csv format)", required=True)
    parser.add_argument(
        "-fc",
        "--file_config",
        dest="tree_conf",
        required=True,
        help='Tree file configuration: "skip lines|separator|id cols|title col" (starting at 0). ' "Like: 1|;|0,4|1",
    )
    parser.add_argument("-u", "--unicity", action="store_true", dest="check_unicity", help="Check code unicity")
    ns = parser.parse_args()
    verbose("Start of %s" % sys.argv[0])
    if "1" in ns.parts:
        if not ns.ref_file or not ns.ref_conf:
            error("Missing -r or -rc parameters for part 1 !")
            parser.print_help()
            sys.exit(1)
        verbose("Reading ref file '{}'".format(ns.ref_file))
        ref_confs = ns.ref_conf.split("|")
        if len(ref_confs) != 4:
            error("rc parameter not well formated: {}".format(ns.ref_conf))
            parser.print_help()
            sys.exit(1)
        skip_lines, ref_id_col, ref_tit_col = int(ref_confs[0]), int(ref_confs[2]), int(ref_confs[3])
        lines = read_csv(ns.ref_file, skip_lines=skip_lines, delimiter=ref_confs[1])
        ref_dic = {}
        for i, line in enumerate(lines, start=skip_lines + 1):
            k = line[ref_id_col]
            if k in ref_dic:
                error("Ref id already exists: {} : {} <=> {}".format(k, ref_dic[k]["t"], line[ref_tit_col]))
            else:
                if not re.match(decimal_identifier, k):
                    error("{}, bad ref identifier value '{}', '{}'".format(i, k, line[ref_tit_col]))
                ref_dic[k] = {"u": "", "t": line[ref_tit_col]}

    if "2" in ns.parts:
        verbose("Reading tree file '{}'".format(ns.tree_file))
        tree_confs = ns.tree_conf.split("|")
        if len(tree_confs) != 4:
            error("fc parameter not well formated: {}".format(ns.tree_conf))
            parser.print_help()
            sys.exit(1)
        skip_lines, tree_tit_col = int(tree_confs[0]), tree_confs[3]
        tree_id_cols = [int(c) for c in tree_confs[2].split(",")]
        lines = read_csv(ns.tree_file, skip_lines=skip_lines, delimiter=tree_confs[1])
        tree_dic = OrderedDict()
        for i, line in enumerate(lines, start=skip_lines + 1):
            for j, id_col in enumerate(tree_id_cols):
                code = line[id_col]
                if not code:
                    continue
                for k in code.split(","):
                    v = tree_tit_col and j == 0 and line[int(tree_tit_col)] or ""
                    if k not in tree_dic:
                        # A. = specific to comblain
                        if not k.startswith("A.") and not re.match(decimal_identifier, k):
                            error("{},{}, bad tree identifier value '{}', '{}'".format(i, id_col, k, v))
                        tree_dic[k] = {"l": i, "c": id_col, "t": v}
                    elif ns.check_unicity:
                        error("{}, id '{}' already found line {}".format(i, k, tree_dic[k]["l"]))
    if "123" == ns.parts:
        verbose("Comparing...")
        for k in sorted(tree_dic):
            tdk = tree_dic[k]
            o_k = k
            if k[0:1] in ("1", "2", "3", "4"):  # must begin with '-'
                k = "-{}".format(k)
            if k in ref_dic:
                ref_dic[k]["u"] = "d"  # direct usage
                if tdk["t"] and tdk["t"] != ref_dic[k]["t"]:
                    print(
                        "{},{}, id '{}', different titles: '{}' <=> '{}'".format(
                            tdk["l"], tdk["c"], k, tdk["t"], ref_dic[k]["t"]
                        )
                    )
            elif not k.startswith("A."):  # specific to comblain
                com = "{},{}, id '{}', not found in ref".format(tdk["l"], tdk["c"], o_k)
                if tdk["t"]:
                    com += " (tit='{}')".format(tdk["t"])
                print(com)
    verbose("End of %s" % sys.argv[0])


def add_parent():
    """Add parent column"""
    parser = argparse.ArgumentParser(description="Analyse code to find parent")
    parser.add_argument(
        "-p", "--parts", dest="parts", help="Run parts: 1 (load codes), 2 (get parent), 3 (write)", default="123"
    )
    parser.add_argument("tree_file", help="Tree file (csv format)")
    parser.add_argument(
        "-c",
        "--config",
        dest="tree_conf",
        required=True,
        help='Tree file configuration: "separator|code col|id col|id parent" (starting at 0). ' "Like: ;|1||",
    )
    parser.add_argument("-u", "--unicity", action="store_true", dest="check_unicity", help="Check code unicity")
    ns = parser.parse_args()
    verbose("Start of %s" % sys.argv[0])
    verbose("Reading tree file '{}'".format(ns.tree_file))
    tree_confs = ns.tree_conf.split("|")
    if len(tree_confs) != 4:
        error("config parameter not well formated: {}".format(ns.tree_conf))
        parser.print_help()
        sys.exit(1)
    sep, code_col, id_col, id_parent = tree_confs[0], int(tree_confs[1]), tree_confs[2], tree_confs[3]
    has_id = id_col != ""
    has_parent = id_parent != ""
    lines = read_csv(ns.tree_file, strip_chars=" ", delimiter=sep)
    code_ids = {}  # store code and id
    all_ids = {}  # store id and code
    titles = lines.pop(0)
    titles.append("Parent")
    cols_nb = len(titles)
    new_lines = [titles]
    if "1" in ns.parts or "2" in ns.parts or "3" in ns.parts:
        for i, line in enumerate(lines, start=1):
            ln_nb = i + 1
            code = line[code_col]
            if not code:
                continue
            if code in code_ids:
                if ns.check_unicity:
                    error("{}, code already found '{}'".format(ln_nb, code))
            else:
                cid = has_id and int(line[int(id_col)]) or i
                code_ids[code] = cid
                all_ids[cid] = code
    next_id = 1

    def get_next_id(nid):
        while nid in all_ids:
            nid += 1
        all_ids.append(nid)
        return nid

    if "2" in ns.parts or "3" in ns.parts:
        for i, line in enumerate(lines, start=1):
            ln_nb = i + 1
            code = line[code_col]
            if not code:
                parent_code = ""
            elif has_parent:
                cid = code_ids[code]
                parent_code = all_ids[cid]
            elif re.match(decimal_identifier, code):
                parent_code = get_decimal_parent(code)
                if parent_code is None:
                    parent_code = ""
                elif False:
                    if parent_code in code_ids:
                        parent_code = code_ids[parent_code]
                    else:
                        parents = get_parents(parent_code)
                        prev_parent_id = ""
                        for level in parents:
                            if level not in code_ids:
                                next_id = get_next_id(next_id)
                                code_ids[level] = next_id
                                new_line = [""] * cols_nb
                                new_line[code_col] = level
                                nid_col = not has_id and -2 or int(id_col)
                                new_line[nid_col] = next_id
                                new_line[-1] = prev_parent_id
                                new_lines.append(new_line)
                                verbose("{}, added decimal level '{}'".format(ln_nb, level))
                            else:
                                prev_parent_id = code_ids[level]
                        parent_code = code_ids[parent_code]
            else:
                error("{}, bad ref identifier value '{}'".format(ln_nb, code))
                parent_code = "!"
            line.append(str(parent_code))
            new_lines.append(line)
    if "3" in ns.parts:
        new_file = ns.tree_file.replace(".csv", "_parent.csv")
        with open(new_file, "wb") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=sep, quoting=csv.QUOTE_NONNUMERIC)
            for line in new_lines:
                csvwriter.writerow(line)
    verbose("End of %s" % sys.argv[0])


def add_archived():
    """Add archived columns to exported file"""
    parser = argparse.ArgumentParser(description="From mixed archived column, add 2 new columns")
    parser.add_argument("-p", "--parts", dest="parts", help="Run parts: 1 (add archived), 2 (write)", default="12")
    parser.add_argument("tree_file", help="Tree file (csv format)")
    parser.add_argument(
        "-c",
        "--config",
        dest="tree_conf",
        required=True,
        help='Tree file configuration: "separator|archived col|sf id col|sf tit col" (starting at 0). ' "Like: ;|1||",
    )
    ns = parser.parse_args()
    verbose("Start of %s" % sys.argv[0])
    verbose("Reading tree file '{}'".format(ns.tree_file))
    tree_confs = ns.tree_conf.split("|")
    if len(tree_confs) != 4:
        error("config parameter not well formated: {}".format(ns.tree_conf))
        parser.print_help()
        sys.exit(1)
    sep, arc_col, id_col, tit_col = tree_confs[0], int(tree_confs[1]), int(tree_confs[2]), int(tree_confs[3])
    lines = read_csv(ns.tree_file, strip_chars=" ", delimiter=sep)
    titles = lines.pop(0)
    titles.extend(["Archivé farde", "Archivé chemise"])
    new_lines = [titles]
    if "1" in ns.parts:
        for i, line in enumerate(lines, start=1):
            ln_nb = i + 1
            archived = line[arc_col]  # '0', '1', 'VRAI', 'FAUX'
            f_arc = sf_arc = ""
            if archived == "VRAI":
                archived = "1"
            elif archived == "FAUX":
                archived = "0"
            if archived not in ("0", "1"):
                error("{}, bad archived value '{}'".format(ln_nb, archived))
            else:
                if line[id_col] or line[tit_col]:  # is subfolder
                    if archived == "1":
                        sf_arc = "1"
                else:  # is folder
                    if archived == "1":
                        f_arc = "1"
            line.extend([f_arc, sf_arc])
            new_lines.append(line)
    if "2" in ns.parts:
        new_file = ns.tree_file.replace(".csv", "_archived.csv")
        with open(new_file, "wb") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=sep, quoting=csv.QUOTE_NONNUMERIC)  # csv.QUOTE_ALL
            for line in new_lines:
                csvwriter.writerow(line)
    verbose("End of %s" % sys.argv[0])
