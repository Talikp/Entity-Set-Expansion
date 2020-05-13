def only_once(f):
    def wrap(*args):
        builder = args[0]
        data_name = "_" + f.__name__
        if hasattr(builder, data_name) and getattr(builder, data_name) is not None:
            raise SyntaxException("{} called more than once".format(f.__name__))
        return f(*args)

    return wrap


class SyntaxException(Exception):
    pass


class SPARQLQueryBuilder:

    def __init__(self):
        self._select = None
        self._distinct = False
        self._orderBy = None
        self._limit = None
        self._groupBy = None
        self._lines = []
        self._filters = []
        self._union = []

    def build(self):
        if self._select is None or len(self._lines) == 0:
            raise SyntaxException

        query = "SELECT"
        if self._distinct:
            query += " DISTINCT"

        query += " " + " ".join(self._select) + " WHERE {\n"

        for line in self._lines:
            query += "\t{}\n".format(line)

        for filter_str in self._filters:
            query += "\tFILTER (\n"
            query += "\t\t{}\n".format(filter_str)
            query += "\t) .\n"

        if len(self._union) > 1:
            query += "\tUNION\n".join(map(lambda line: "\t{}\n".format(line), self._union))

        query += "}"
        query += "" if self._groupBy is None else " GROUP BY {}".format(" ".join(self._groupBy))
        query += "" if self._orderBy is None else " ORDER BY {}".format(self._orderBy)
        query += "" if self._limit is None else " LIMIT {}".format(self._limit)

        return query

    def distinct(self):
        self._distinct = True
        return self

    def add(self, line):
        self._lines.append(line)
        return self

    def filter(self, line):
        self._filters.append(line)
        return self

    def union(self, line):
        if type(line) is str:
            self._union.append(line)
        elif type(line) is list:
            self._union.extend(line)
        return self

    @only_once
    def select(self, *args):
        self._select = args
        return self

    @only_once
    def limit(self, limit_value):
        self._limit = int(limit_value)
        return self

    @only_once
    def orderBy(self, orderBy):
        self._orderBy = orderBy
        return self

    @only_once
    def groupBy(self, *args):
        self._groupBy = args
        return self
