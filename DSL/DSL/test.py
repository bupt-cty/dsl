import unittest
import yaml
import sys
from src import ConfigLoader, Command, RunPy, Interpreter
from src.ply import Lexer, Parser
from schema import SchemaError

goodconf = ConfigLoader()
goodconf.load('./src/data/default_config.yaml')


class ConfigLoaderTest(unittest.TestCase):
    '''
    测试ConfigLoader是否能够正确加载配置并校验配置是否合法
    '''
    def test_parse_job2(self):
        conf = ConfigLoader()
        conf.load('./config.yaml')
        lexer = Lexer(conf)
        lexer.load('./jobs/example.job')
        parser = Parser(conf, lexer)
        with open('./jobs/example.job', 'r', encoding='utf-8') as f:
            p = parser.parseStr(f.read())
            p.print()

    def test_wrong_value_type(self):
        conf = ConfigLoader()
        self.assertRaises(SchemaError, conf.load,
                          'tests/wrong_value_type.yaml')

    def test_good_value(self):
        conf = ConfigLoader()
        path = 'tests/good_value.yaml'
        conf.load(path)
        with open(path, 'r', encoding='utf8') as f:
            right = yaml.load(f, yaml.CLoader)
        right.update({'pwd': '.'})
        self.assertEqual(conf.getConfig(), right, 'Config Loaded Incorrectly.')
        self.assertEqual(conf.getConfig().get('pwd'), '.',
                         'Failed to extract default value.')


class LexerTest(unittest.TestCase):
    '''
    测试词法分析模块能否正确获取token并识别出错误token
    '''
    def get_token(self, str):
        conf = ConfigLoader()
        conf.load('tests/good_value.yaml')
        lexer = Lexer(conf)
        lexer.load_str(str)
        return lexer.token()

  

class ParserTest(unittest.TestCase):
    '''
    测试语法分析程序能否正确解析脚本文件
    '''
    def test_parse_job(self):
        conf = ConfigLoader()
        conf.load('./config.yaml')
        lexer = Lexer(conf)
        lexer.load('./jobs/example.job')
        parser = Parser(conf, lexer)
        with open('./jobs/example.job', 'r', encoding='utf-8') as f:
            p = parser.parseStr(f.read())
            p.print()

    def test_parse_job2(self):
        conf = ConfigLoader()
        conf.load('./config.yaml')
        lexer = Lexer(conf)
        lexer.load('./jobs/example_nl.job')
        parser = Parser(conf, lexer)
        with open('./jobs/example_nl.job', 'r', encoding='utf-8') as f:
            p = parser.parseStr(f.read())
            p.print()


class RuntimeTest(unittest.TestCase):
    '''
    测试Runtime的设置变量，提取关键词功能是否正常
    '''
    def test_runtime_setvar(self):
        rt = Command("123456", goodconf)
        rt.assign('asd', 123)
        rt.assign('_ret', None)
        self.assertEqual(rt.getvar('asd'), '123')
        self.assertEqual(rt.getvar('_ret'), 'None')

    def test_runtime_extract(self):
        rt = Command("123456", goodconf)
        rt._extractKeywords('爱动机哦三大赛充值啊所拆机就')
        self.assertEqual(rt.getvar('_input_keyword'), '充值')
        rt._extractNumbers('爱动机哦123123拆机就')
        self.assertEqual(rt.getvar('_input_number'), '123123')



class MainTest(unittest.TestCase):
    '''
    测试脚本运行全过程
    '''

    def test_main_test2(self):
        stdout = sys.stdout
        stdin = sys.stdin

        sys.stdout = open("./tests/out.txt", 'w+', encoding='utf-8')
        sys.stdin = open('./tests/in2.txt', 'r', encoding='utf-8')
        interpreter = Interpreter(goodconf)
        runtime = Command('test', goodconf, enable_timeout=False)
        interpreter.accept(runtime)
    
        sys.stdout.close()
        sys.stdin.close()
        sys.stdout = stdout
        sys.stdin = stdin
        with open('./tests/out.txt', encoding='utf-8') as f:
            out = f.read()
        with open('./tests/example_output3.txt', encoding='utf-8') as f:
            example_out = f.read()

        self.assertEqual(out, example_out)

if __name__ == "__main__":
    unittest.main()
