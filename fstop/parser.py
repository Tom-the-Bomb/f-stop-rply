from PIL import Image as PIL_Image
from rply import ParserGenerator

from .objects import Image

parser = ParserGenerator(
    [
        'INTEGER', 'FLOAT', 'STRING', 'NUMBER_TUPLE', 'EQUAl',
        'LEFT_PAREN', 'RIGHT_PAREN', 
        'OPEN', 'AS', 'SAVE', 'CLOSE', 'SHOW', 'BLEND', 'RESIZE', 'ROTATE', 'MASK', 'CONVERT', 'CLONE', 'PUTPIXEL',
        'NEW', 'WIDTH', 'HEIGHT', 'COLOR', 'ALPHA', 'PASTE', 'SIZE', 'MODE',
        'VARIABLE', 'COMMA', 'ON', 'ECHO',
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
@parser.production('string : MODE variable')
def string(p: list) -> str:
    if len(p) == 1:
        return p[0].getstr().strip("'").strip('"')
    else:
        if not (img := parser.env.get(p[-1])):
            raise NameError("Undefined image '%s'" % p[-1])
        else:
            return img.image.mode

@parser.production('number : INTEGER')
@parser.production('number : WIDTH variable')
@parser.production('number : HEIGHT variable')
def integer(p: list) -> int:
    if len(p) == 1:
        return int(p[0].getstr())
    else:
        if not (img := parser.env.get(p[-1])):
            raise NameError("Undefined image '%s'" % p[-1])
        else:
            return (
                img.image.width if p[0].gettokentype() == "WIDTH" else img.image.height
            )

@parser.production('float : FLOAT')
def float_(p: list) -> float:
    return float(p[0].getstr())
    
@parser.production('variable : VARIABLE')
def variable_name(p: list) -> str:
    return p[0].getstr()

@parser.production('ntuple : NUMBER_TUPLE')
@parser.production('ntuple : SIZE variable')
def num_tuple(p: list) -> tuple:
    if len(p) == 1:
        return tuple(map(int, p[0].getstr().strip("() \n\r,").split(",")))
    else:
        if not (img := parser.env.get(p[-1])):
            raise NameError("Undefined image '%s'" % p[-1])
        else:
            return img.image.size

@parser.production('expr : BLEND variable COMMA variable ALPHA float AS variable')
def blend(p: list) -> Image:
    backg, overlay, alpha, name = p[1], p[3], p[-3], p[-1]

    if not (img1 := parser.env.get(backg)):
        raise NameError("Undefined image '%s'" % backg)
    if not (img2 := parser.env.get(overlay)):
        raise NameError("Undefined image '%s'" % overlay)

    img = PIL_Image.blend(img1.image, img2.image, alpha=alpha)
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

@parser.production('expr : CLONE variable AS variable')
def clone_statement(p: list) -> Image:
    if not (img := parser.env.get(p[1])):
        raise NameError("Undefined image '%s'" % p[1])
    else:
        name = p[-1]
        clone = img.image.copy()
        image = Image(clone, name=name)
        parser.env[name] = image 
        return image

@parser.production('expr : CONVERT variable string')
def convert_statement(p: list) -> Image:
    if not (img := parser.env.get(p[1])):
        raise NameError("Undefined image '%s'" % p[1])
    else:
        img.image = img.image.convert(p[-1])
        parser.env[p[1]] = img
    return None

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

@parser.production('expr : RESIZE variable ntuple')
def resize_statement(p: list) -> None:
    if not (img := parser.env.get(p[1])):
        raise NameError("Undefined image '%s'" % p[1])
    else:
        img.image = img.image.resize(p[-1])
        parser.env[p[1]] = img
    return None

@parser.production('expr : ROTATE variable number')
def rotate_statement(p: list) -> None:
    if not (img := parser.env.get(p[1])):
        raise NameError("Undefined image '%s'" % p[1])
    else:
        img.image = img.image.rotate(p[-1])
        parser.env[p[1]] = img
    return None

@parser.production('expr : PASTE variable ON variable')
@parser.production('expr : PASTE variable ON variable ntuple')
@parser.production('expr : PASTE variable ON variable MASK variable ntuple')
def paste_statement(p: list) -> None:
    image, snippet = p[1], p[3]

    if not (img1 := parser.env.get(image)):
        raise NameError("Undefined image '%s'" % image)
    if not (img2 := parser.env.get(snippet)):
        raise NameError("Undefined image '%s'" % snippet)

    xy = (0, 0) if len(p) == 4 else p[-1]
    mask = p[-2] if len(p) == 7 else None
    img2.image.paste(img1.image, xy, mask=mask)
    parser.env[img2] = img2
    return None

@parser.production('expr : PUTPIXEL variable ntuple COLOR ntuple')
@parser.production('expr : PUTPIXEL variable ntuple COLOR number')
def putpixel(p: list) -> None:
    coords, color = p[-3], p[-1]
    if not (img := parser.env.get(p[1])):
        raise NameError("Undefined image '%s'" % p[1])
    else:
        img.image.putpixel(coords, color)
        parser.env[img] = img
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

@parser.production('expr : ECHO string')
@parser.production('expr : ECHO number')
@parser.production('expr : ECHO float')
@parser.production('expr : ECHO variable')
@parser.production('expr : ECHO ntuple')
def echo(p: list) -> None:
    print(p[-1])
    return None