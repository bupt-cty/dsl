from functools import reduce
from src import ConfigLoader
from src import Command
from src.ply.SyntaxTree import SyntaxTree
from .ply import Lexer
from .ply import Parser
from src import RunPy
from logging import getLogger

logger = getLogger('Interpreter')
runpy = RunPy.getInstance()


class Interpreter:
    def __init__(self, configLoader: ConfigLoader):
        self._lexer = Lexer(configLoader)
        self._parser = Parser(configLoader, self._lexer)
        self._config = configLoader
        runpy.init(self._config)
        self.job = ''
        self.ast = None
        self.steps = {}
        self._stop = False

        self._load_job()
        self._parse()

    def accept(self, runtime: Command):
        """
        接受一个Runtime对象，并开始从Main step运行脚本
        :param runtime Runtime: 
        """
        self._stop = False
        self.runtime = runtime
        self.run()

    def run(self):
        """
        开始运行脚本
        :raises RuntimeError: 没有接受Runtime对象
        :raises RuntimeError: 没有定义Main step
        """
        if not self.runtime or not self.ast:
            if self.ast:
                self.ast.print()
            raise RuntimeError("Must call setRuntime and load_job before Run")
        logger.info("Begin running...")
        if 'Main' not in self.steps:
            raise RuntimeError("Entry step Main not defined")
        self._runStep(self.steps['Main'])

    def stop(self):
        # 请求停止脚本执行

        self._stop = True

    def _getStep(self, stepname):
        # 根据步骤名称获取步骤定义
        step = self.steps.get(stepname, None)
        if not step:
            raise RuntimeError(f"Undefined step {stepname}")
        return step

    def _runStep(self, step: SyntaxTree, *args):
        # 执行指定的步骤
        self._setargs(self, *args)
        for expression in step.childs:
            self._exec(expression)

    def _exec(self, expr: SyntaxTree):
        # 执行一个 AST 节点代表的表达式
        if self._stop:
            return
        if expr.type[0] != 'expression':
            logger.error('Not an expression')
        match expr.type[1]:
            case 'call':
                self._runStep(self._getStep(expr.childs[0].type[1]), *self._eval(expr.childs[1]))
            case 'assign':
                self.runtime.assign(expr.type[2], self._eval(expr.childs[0]))
            case 'speak':
                self.runtime.speak(self._eval(expr.childs[0]))
            case 'callpy':
                self._callpy(expr.childs[0].type[1], *self._eval(expr.childs[1]))
            case 'beep':
                self.runtime.beep()
            case 'wait':
                self.runtime.wait(self._eval(expr.childs[0]))
            case 'hangup':
                self.stop()
                self.runtime.hangup()
            case 'switch':
                self._exec_switch(expr)

    def _callpy(self, funcName, *args):
        # 调用一个 Python 函数并处理返回值
        ret = runpy.callFunc(funcName, *args)
        self.runtime.assign('_ret', ret)

    def _exec_switch(self, expr: SyntaxTree):
        # 执行 switch 表达式的逻辑
        condition = self.runtime.getvar(expr.type[2])
        cases = [child.type[1] for child in expr.childs if child.type[0] == 'case']
        default = expr.childs[-1] if expr.childs[-1].type[0] == 'default' else None
        match = -1
        for i in range(len(cases)):
            if condition == cases[i]:
                match = i
                break
        if match == -1 and default:
            return self._exec(default.childs[0])
        elif match != -1:
            return self._exec(expr.childs[match].childs[0])

    def _eval(self, term: SyntaxTree):
        # 评估一个 AST 节点，并返回结果
        match term.type[0]:
            case 'var':
                return self.runtime.getvar(term.type[1])
            case 'str':
                return term.type[1]
            case 'terms':
                return reduce(lambda x, y: x+self._eval(y), term.childs, '')
            case 'va_args':
                return [self._eval(x) for x in term.childs]
            case _:
                raise RuntimeError("eval an unknown SyntaxTree")

    def _setargs(self, *args):
        # 设置运行时参数
        for i in range(len(args)):
            self.runtime.assign(str(i), args[i])

    def _load_job(self):
        # 加载并读取脚本文件
        with open(self._config.getJobConfig().get('path'), 'r', encoding='utf-8') as f:
            self.job = f.read()
        self._lexer.load_str(self.job)

    def _parse(self):
        # 解析脚本内容，构建 AST
        logger.info("Begin parsing job file...")
        if self.job == '':
            raise RuntimeError('job is empty')
        self.ast = self._parser.parseStr(self.job)
        for stepdecl in self.ast.childs:
            self.steps[stepdecl.type[1]] = stepdecl