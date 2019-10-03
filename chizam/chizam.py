from sly import Lexer
from sly import Parser


class ChizamLexer(Lexer):
    ignore = '\t '
    literals = {'=', '+', '-', '/', '*', '(', ')', ',', ';', '%'}
    tokens = {NAME, NUMBER, DO, ELSE, FOR, FUNC, TO, ARROW,
              STRING, IF, EQEQ, LD, GD, GDEQ, LDEQ, DISPLAY}

    # token definitions
    IF = r'if'
    DO = r'do'
    ELSE = r'else'
    FOR = r'for'
    FUNC = r'func'
    TO = r'to'
    ARROW = r'->'
    NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    STRING = r'\".*?\"'
    DISPLAY = r'display'

    EQEQ = r'=='
    LD = r'<'
    GD = r'>'
    LDEQ = r'<='
    GDEQ = r'>='

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r'#.*')
    def COMMENT(self, t):
        pass

    @_(r'\n+')
    def newline(self, t):
        self.lineno = t.value.count('\n')


class ChizamParser(Parser):
    tokens = ChizamLexer.tokens

    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('right', 'UMINUS'),
    )

    def __init__(self):
        self.env = {}

    @_('')
    def statement(self, p):
        pass

    @_('FOR var_assign TO expr DO statement')
    def statement(self, p):
        return ('for_loop', ('for_loop_setup', p.var_assign, p.expr), p.statement)

    @_('IF condition DO statement ELSE statement')
    def statement(self, p):
        return ('if_stmt', p.condition, ('branch', p.statement0, p.statement1))

    @_('FUNC NAME "(" ")" ARROW statement')
    def statement(self, p):
        return('func_def', p.NAME, p.statement)

    @_('NAME "(" ")"')
    def statement(self, p):
        return ('func_call', p.NAME)

    @_('expr EQEQ expr')
    def condition(self, p):
        return ('condition_eqeq', p.expr0, p.expr1)

    @_('expr EQEQ expr')
    def expr(self, p):
        return ('condition_eqeq', p.expr0, p.expr1)

    @_('expr LD expr')
    def condition(self, p):
        return ('condition_ld', p.expr0, p.expr1)

    @_('expr GD expr')
    def condition(self, p):
        return ('condition_gd', p.expr0, p.expr1)

    @_('expr LDEQ expr')
    def condition(self, p):
        return ('condition_ldeq', p.expr0, p.expr1)

    @_('expr GDEQ expr')
    def condition(self, p):
        return ('condition_gdeq', p.expr0, p.expr1)

    @_('var_assign')
    def statement(self, p):
        return (p.var_assign)

    @_('NAME "=" expr')
    def var_assign(self, p):
        return ('var_assign', p.NAME, p.expr)

    @_('NAME "=" STRING')
    def var_assign(self, p):
        return ('var_assign', p.NAME, p.STRING)

    @_('expr')
    def statement(self, p):
        return (p.expr)

    @_('expr "+" expr')
    def expr(self, p):
        return ('add', p.expr0, p.expr1)

    @_('expr "-" expr')
    def expr(self, p):
        return ('sub', p.expr0, p.expr1)

    @_('expr "*" expr')
    def expr(self, p):
        return ('mul', p.expr0, p.expr1)

    @_('expr "/" expr')
    def expr(self, p):
        return ('div', p.expr0, p.expr1)

    @_('expr "%" expr')
    def expr(self, p):
        return ('mod', p.expr0, p.expr1)

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return p.expr

    @_('NAME')
    def expr(self, p):
        return ('var', p.NAME)

    @_('NUMBER')
    def expr(self, p):
        return ('num', p.NUMBER)

    @_('STRING')
    def statement(self, p):
        return ('str', p.STRING)

    @_('DISPLAY "(" statement ")"')
    def statement(self, p):
        return ('display', p.statement)


class ChizamExecute:
    def __init__(self, tree, env):
        self.env = env
        result = self.walkTree(tree)
        if result is not None and isinstance(result, int):
            print(result)
        if isinstance(result, str) and result[0] == '"':
            print(result)

    def walkTree(self, node):
        if isinstance(node, int) or isinstance(node, str):
            return node

        if node is None:
            return None

        if node[0] == 'program':
            if node[1] == None:
                self.walkTree(node[2])
            else:
                self.walkTree(node[1])
                self.walkTree(node[2])

        if node[0] == 'num' or node[0] == 'str':
            return node[1]

        if node[0] == 'if_stmt':
            result = self.walkTree(node[1])
            if result:
                return self.walkTree(node[2][1])

            return self.walkTree(node[2][2])

        if node[0] == 'func_def':
            self.env[node[1]] = node[2]

        if node[0] == 'func_call':
            try:
                return self.walkTree(self.env[node[1]])
            except LookupError:
                print("Undefined function '%s'" % node[1])
                return None

        if node[0] == 'condition_eqeq':
            return self.walkTree(node[1]) == self.walkTree(node[2])
        if node[0] == 'condition_gdeq':
            return self.walkTree(node[1]) >= self.walkTree(node[2])
        if node[0] == 'condition_ldeq':
            return self.walkTree(node[1]) <= self.walkTree(node[2])
        if node[0] == 'condition_ld':
            return self.walkTree(node[1]) < self.walkTree(node[2])
        if node[0] == 'condition_gd':
            return self.walkTree(node[1]) > self.walkTree(node[2])

        if node[0] == 'add':
            return self.walkTree(node[1]) + self.walkTree(node[2])
        elif node[0] == 'sub':
            return self.walkTree(node[1]) - self.walkTree(node[2])
        elif node[0] == 'mul':
            return self.walkTree(node[1]) * self.walkTree(node[2])
        elif node[0] == 'div':
            return self.walkTree(node[1]) / self.walkTree(node[2])
        elif node[0] == 'mod':
            return self.walkTree(node[1]) % self.walkTree(node[2])

        if node[0] == 'var_assign':
            value = self.walkTree(node[2])
            self.env[node[1]] = value
            print(value)
            return node[1]

        if node[0] == 'var':
            try:
                return self.env[node[1]]
            except LookupError:
                print("variable with name '"+node[1]+"' is undefined!")
                return None

        if node[0] == 'for_loop':
            if node[1][0] == 'for_loop_setup':
                loop_setup = self.walkTree(node[1])
                loop_count = self.env[loop_setup[0]]
                loop_limit = loop_setup[1]

                for i in range(loop_count + 1, loop_limit + 1):
                    res = self.walkTree(node[2])
                    if res is not None:
                        print(res)
                    self.env[loop_setup[0]] = i

                del self.env[loop_setup[0]]

        if node[0] == 'for_loop_setup':
            return (self.walkTree(node[1]), self.walkTree(node[2]))

        # if node[0] == 'display':
        #     return((self.walkTree(node[1]))


if __name__ == '__main__':
    lexer = ChizamLexer()
    parser = ChizamParser()
    env = {}
    while True:
        try:
            text = input('chizam > ')
        except EOFError:
            break
        if text:
            tree = parser.parse(lexer.tokenize(text))
            ChizamExecute(tree, env)
