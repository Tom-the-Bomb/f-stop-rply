from PIL import Image as PIL_Image
from rply import ParserGenerator

from .objects import Image

parser = ParserGenerator(
    [
        'INTEGER', 'FLOAT', 'STRING', 'NUMBER_TUPLE',
        'LEFT_PAREN', 'RIGHT_PAREN', 
        'OPEN', 'AS', 'SAVE', 'CLOSE', 'SHOW', 'BLEND',
        'NEW', 'WIDTH', 'HEIGHT', 'COLOR', 'ALPHA', 
        'VARIABLE', 'COMMA',
        'INVERT', 'SOLAR', 'MIRROR', 'FLIP',
    ],
    
    precedence = [
        ('left', ['OPEN', 'SAVE', 'AS']),
        ('left', ['INVERT'])
    ],
)

@parser.production("main : statements")
def program(p: list):
    return p[0]

@parser.production("statements : statements expr")
def statements(p: list):
    return p[0] + [p[1]]

@parser.production("statements : expr")
def expr(p: list):
    return [p[0]]

@parser.production('string : STRING')
def string(p: list) -> str:
    return p[0].getstr().strip("'").strip('"')

@parser.production('number : INTEGER')
def integer(p: list) -> int:
    return int(p[0].getstr())

@parser.production('float : FLOAT')
def float_(p: list) -> float:
    return float(p[0].getstr())
    
@parser.production('variable : VARIABLE')
def variable_name(p: list) -> str:
    return p[0].getstr()

@parser.production('ntuple : NUMBER_TUPLE')
def num_tuple(p: list) -> tuple:
    return tuple(p[0].strip("() \n\r,").split(","))

@parser.production('expr : BLEND variable COMMA variable AS variable')
@parser.production('expr : BLEND variable COMMA variable ALPHA float AS variable')
def blend(p: list) -> Image:
    backg, overlay, name = p[1], p[3], p[-1]
    alpha = p[5] if len(p) == 8 else None
    img = PIL_Image.blend(backg, overlay, alpha=alpha)
    image = Image(img, name=name)
    parser.env[name] = image
    return image

@parser.production('expr : NEW string LEFT_PAREN number COMMA number RIGHT_PAREN AS variable')
@parser.production('expr : NEW string LEFT_PAREN number COMMA number COLOR ntuple RIGHT_PAREN AS variable')
@parser.production('expr : NEW string LEFT_PAREN number COMMA number COLOR number RIGHT_PAREN AS variable')
def new_statement(p: list) -> Image:
    mode, width, height, name = p[1], p[3], p[5], p[-1]
    color = p[7] if len(p) == 11 else 0
    img = PIL_Image.new(mode, (width, height), color)
    image = Image(img, name=name)
    parser.env[name] = image
    return image

@parser.production('expr : OPEN string AS variable')
def open_statement(p: list) -> Image:
    filename, name = p[1], p[-1]
    img = PIL_Image.open(filename)
    image = Image(img, name=name)
    parser.env[name] = image
    return image

@parser.production('expr : SAVE variable string')
def save_statement(p: list) -> str:
    if not (img := parser.env.get(p[-2])):
        raise NameError("Undefined image '%s'" % p[-2])
    else:
        img.image.save(p[-1])
    return p[-1]

@parser.production('expr : CLOSE variable')
def close_statement(p: list) -> None:
    if not (img := parser.env.get(p[-1])):
        raise NameError("Undefined image '%s'" % p[-1])
    else:
        img.image.close()
    return None

@parser.production('expr : SHOW variable')
@parser.production('expr : SHOW variable string')
def show_statement(p: list) -> None:
    if not (img := parser.env.get(p[1])):
        raise NameError("Undefined image '%s'" % p[1])
    else:
        title = p[-1] if len(p) == 3 else None
        img.image.show(title=title)
    return None