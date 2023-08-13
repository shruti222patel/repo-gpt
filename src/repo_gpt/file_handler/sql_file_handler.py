from typing import List

import sqlglot
from sqlglot.expressions import CTE, Delete, Func, Insert, Select, Update

from .abstract_handler import ParsedCode


class SqlFileHandler:
    def extract_code(self, filepath) -> List[ParsedCode]:
        with open(filepath, "r") as file:
            sql = file.read()

        parsed = sqlglot.parse(sql)

        parsed_statements = []
        for i, statement in enumerate(parsed, start=1):
            if isinstance(statement, (Select, Update, Delete, Insert, CTE, Func)):
                parsed_statements.append(
                    ParsedCode(
                        name=str(i),
                        code_type=type(statement).__name__,
                        code=str(statement),
                        summary=None,
                        inputs=None,  # TODO: should this include ctes?
                        outputs=None,
                    )
                )

        return parsed_statements
