# -*- coding: utf-8 -*-

from collective.classification.tree import utils
from operator import attrgetter
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from unidecode import unidecode
from zope.component import queryMultiAdapter


class TreeSearchHandler(object):
    def __init__(self, context):
        self.context = context

    def search(self, query):
        self.query = query
        raw_results = utils.iterate_over_tree(self.context)
        filtered_data = self._order(self._filter(raw_results))
        start, end = self._limits
        return len(raw_results), len(filtered_data), filtered_data[start:end]

    @property
    def _limits(self):
        start = self._to_int(self.query.get("start", "0"), 0)
        length = self._to_int(self.query.get("length", "10"), 10)
        return start, start + length

    @staticmethod
    def _to_int(value, default):
        """Convert a string to an integer, if the value can not be converted
        the default value is returned"""
        try:
            return int(value)
        except ValueError:
            return default

    def _get_columns(self, searchable=None, orderable=None):
        """Return the known columns keys"""
        columns = []
        finished = False
        idx = 0
        while finished is False:
            name = self.query.get("columns[{0}][data]".format(idx))
            if name is None:
                finished = True
                break
            if searchable is True and self.query.get("columns[{0}][searchable]".format(idx)) != "true":
                name = None
            if orderable is True and self.query.get("columns[{0}][searchable]".format(idx)) != "true":
                name = None
            if name is not None:
                columns.append(name)
            idx += 1
        return columns

    def _filter(self, results):
        regex = self.query.get("search[regex]", "false") == "true"
        search = unidecode(self.query.get("search[value]", "").decode("utf8")).lower()
        if not search:
            return results
        columns = self._get_columns(searchable=True)
        return [r for r in results if self._object_filter(r, columns, search, regex)]

    @staticmethod
    def _object_filter(obj, columns, search, regex):
        if regex is True:
            for key in columns:
                if search in unidecode(getattr(obj, key) or u"").lower():
                    return True
            return False
        else:
            for key in columns:
                if search == unidecode(getattr(obj, key) or u"").lower():
                    return True
            return False

    def _order(self, results):
        idx = self._to_int(self.query.get("order[0][column]", "0"), 0)
        reverse = self.query.get("order[0][dir]", "asc") == "desc"
        columns = self._get_columns()
        if not columns:
            return results
        order_column = columns[idx]
        return sorted(results, key=attrgetter(order_column), reverse=reverse)


class TreeGet(Service):
    """Service that return a given tree that can be handled by datatables"""

    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        result = {}
        if "draw" in query:
            result["draw"] = query.pop("draw")
        handler = TreeSearchHandler(self.context)
        result["recordsTotal"], result["recordsFiltered"], data = handler.search(query)
        result["data"] = [queryMultiAdapter((o, self.request), ISerializeToJson)() for o in data]
        return result
