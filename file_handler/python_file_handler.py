from file_handler.abstract_handler import AbstractHandler
from file_handler.handler_registry import register_handler


@register_handler(".py")
class PythonFileHandler(AbstractHandler):
    @staticmethod
    def get_function_name(code):
        assert code.startswith("def ")
        return code[len("def ") : code.index("(")]

    @staticmethod
    def get_until_no_space(all_lines, i) -> str:
        ret = [all_lines[i]]
        for j in range(i + 1, i + 10000):
            if j < len(all_lines):
                if len(all_lines[j]) == 0 or all_lines[j][0] in [" ", "\t", ")"]:
                    ret.append(all_lines[j])
                else:
                    break
        return "\n".join(ret)

    def extract_code(self, filepath):
        whole_code = open(filepath).read().replace("\r", "\n")
        all_lines = whole_code.split("\n")
        for i, l in enumerate(all_lines):
            if l.startswith("def "):
                code = self.get_until_no_space(all_lines, i)
                function_name = self.get_function_name(code)
                yield {"code": code, "function_name": function_name}
