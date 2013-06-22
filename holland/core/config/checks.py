"""
    holland.core.config.checks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    DSL parser for parsing configspec checks.

    This implementation was heavily derived from the ideas and implementation
    in `ConfigObj <http://www.voidspace.org.uk/python/configobj.html>_`

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

from re import Scanner
from operator import itemgetter
from holland.core.config.util import unquote, missing

__all__ = [
    'Check',
    'CheckError',
]

class Token(object):
    """Lexer token"""
    def __init__(self, text, token_id, value, position=()):
        self.text = text
        self.token_id = token_id
        self.value = value
        self.position = position

    def __repr__(self):
        return 'Token(text=%r, type=%r, value=%r, position=%d-%d)' % \
                (self.text, self.token_id, self.value,
                 self.position[0], self.position[1])


def create_token(token_id, conversion=str):
    """Create a token with the given id

    This will set the token's value attribute to the text value
    after processing the the conversion method

    This method is a decorator for a standard f(scanner,value)
    tokenization dispatch function from re.Scanner

    :returns: tokenization function
    """
    def generate(scanner, value):
        """Generate the actual token

        This initializes a new Token instance with the token_id
        from the outer scope and sets the value based on the input
        from re.Scanner

        :returns: Token instance
        """
        return Token(token_id=token_id,
                     text=value,
                     value=conversion(value),
                     position=scanner.match.span())
    return generate


class Lexer(object):
    """Simple lexer of an iterable of tokens"""
    def __init__(self, iterable):
        self.iterable = iter(iterable)

    def expect(self, *token_ids):
        """Fetch the next token and raise a CheckParseError if its
        type is not one of the provided, expected token ids

        :returns: next Token instance
        """
        token = self.next()
        if token.token_id not in token_ids:
            raise CheckParseError("Expected one of %r but got %r" %
                             (token_ids, token))
        return token

    def next(self):
        """Fetch the next token

        :returns: Token instance
        """
        try:
            tok = self.iterable.next()
            return tok
        except StopIteration:
            raise CheckParseError("Reached end-of-input when reading token")

    def __iter__(self):
        return self

class CheckError(Exception):
    """Raise when an error is occured during a check"""

class CheckParseError(CheckError):
    """Raised when an error is encountered during parsing a check string"""


class CheckParser(object):
    """Parse the check DSL supported by ``Configspec``"""
    T_ID        = 1
    T_STR       = 2
    T_NUM       = 4
    T_SYM       = 16

    # rule patterns
    name_re     = r'[0-9a-zA-Z_-][a-zA-Z0-9_-]*[a-zA-Z_-]'
    str_re      = (r"'([^'\\]*(?:\\.[^'\\]*)*)'"r'|"([^"\\]*(?:\\.[^"\\]*)*)"')
    float_re    = r'(?<!\.)\d+\.\d+'
    int_re      = r'\d+'
    sym_re      = r'[()=,]'
    space_re    = r'\s+'

    # scanner
    scanner = Scanner([
        (name_re, create_token(T_ID)),
        (str_re, create_token(T_STR, unquote)),
        (float_re, create_token(T_NUM, float)),
        (int_re, create_token(T_NUM, int)),
        (sym_re, create_token(T_SYM)),
        (space_re, None)
    ])

    @classmethod
    def tokenize(cls, check):
        """Tokenize a check into its constituent parts.

        This method is used by ``CheckParser.parse()`` and should otherwise
        only be used for testing or debugging check tokenizing behavior

        :returns: list of ``Token`` instances
        """
        tokens, remainder = cls.scanner.scan(check)


        if remainder:
            offset = len(check) - len(remainder)
            raise CheckParseError("Unexpected character at offset %d\n%s\n%s" %
                                  (offset, check, " "*offset + "^"))

        return tokens

    @classmethod
    def parse(cls, check):
        """Parse a check

        This is primarily used implicitly by ``Configspec`` to lookup checks by name
        in its own registry.

        :returns: tuple (check_name, args, kwargs)
        """
        tokens = cls.tokenize(check)

        lexer = Lexer(tokens)

        method = lexer.next()
        if method.token_id != cls.T_ID:
            raise CheckParseError("Expected identifier as first token in check "
                             "string but got %r" % method.token_id)

        # bare-name check
        try:
            token = lexer.next()
        except CheckParseError:
            return method.value, (), {}

        if token.text != '(':
            raise CheckParseError("Expected '(' as token following method name")

        args, kwargs = cls._parse_argument_list(lexer)

        return method.value, args, kwargs

    @classmethod
    def _parse_argument_list(cls, lexer):
        """Parse a list of arguments starting immediately after the open '('"""
        args = []
        kwargs = {}
        for token in lexer:
            if token.text == ')':
                break
            if token.token_id not in (cls.T_ID, cls.T_STR, cls.T_NUM):
                raise CheckParseError("Unexpected token %r" % token)

            arg = cls._parse_expression(lexer, token)
            token = lexer.expect(cls.T_SYM)
            if token.text == '=':
                value = cls._parse_expression(lexer, lexer.next())
                kwargs[arg] = value
                token = lexer.next()
            else:
                args.append(arg)

            if token.text != ',':
                break

        if token.text != ')':
            raise CheckParseError("Expected check expression to end with ')' "
                             "but got %r" % token)
        return tuple(args), kwargs

    @classmethod
    def _parse_expression(cls, lexer, token):
        """Parse a single expression

        This will either be a literal and identifier or an
        identifer=literal|identifier keyword pair
        """
        if token.token_id in (cls.T_STR, cls.T_NUM):
            # literal value
            return token.value
        elif token.token_id == cls.T_ID and token.text != 'list':
            if token.text == 'None':
                return None
            return token.value
        else:
            return cls._parse_list_expr(lexer)

    @classmethod
    def _parse_list_expr(cls, lexer):
        """Parse a list expression

        This starts immediately after the 'list' token is detected.
        A list expression may only contain expressions but may not contain
        keyword arguments.

        :returns: list of elements the comprise the expression
        """
        args = []
        token = lexer.next()
        if token.text != '(':
            raise CheckParseError("Expected '(' but got %r instead" % token)
        args, kwargs = cls._parse_argument_list(lexer)
        if kwargs:
            raise CheckError("list expressions may not contain keyword "
                             "arguments")
        return list(args)

class Check(tuple):
    """Represents a parse Check string

    A check is a python like mini-language defining a name and
    set of arguments and keyword arguments that define a series
    of constraints for some data check.  These are intrepreted
    by a higher level Validator object.

    Check BNF:

    <check>             ::= <name> <arguments>
    <arguments>         ::= ( <argument-list> ) | ""
    <argument-list>     ::= <argument> | <argument>,<argument>
    <argument>          ::= <identifier> | <integer> | <float> | <string>
    <identifier>        ::= (<letter>|"_") (<letter>|<digit>|"_")
    <integer>           ::= <digit> <digit>*
    <float>             ::= <digit>+ "." <digit>*
    <string>            ::= "'" stringitem* "'" | '"' stringitem* '"'
    <stringitem>        ::= <stringchar> | <escapeseq>
    <stringchar>        ::= <any source character except "\\" or newline or the
                             quote>
    <escapeseq>         ::= "\\" <any ASCII character>
    """

    name = property(itemgetter(0))
    args = property(itemgetter(1))
    kwargs = property(itemgetter(2))
    default = property(itemgetter(3))
    aliasof = property(itemgetter(4))

    @classmethod
    def parse(cls, check):
        """Parse a check and return a new Check instance"""
        name, args, kwargs = CheckParser.parse(check)
        default = kwargs.pop('default', missing)
        aliasof = kwargs.pop('aliasof', missing)
        return cls((name, args, kwargs, default, aliasof))

    @property
    def is_alias(self):
        """Boolean flag whether this check is an alias for another check"""
        return self.aliasof is not missing

    def __repr__(self):
        return "Check(name=%r, args=%r, kwargs=%r, default=%r, aliasof=%r)" % \
                (self.name, self.args, self.kwargs, self.default, self.aliasof)
