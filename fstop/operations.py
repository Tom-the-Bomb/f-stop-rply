
from typing import Callable, TypeVar
from functools import wraps

from PIL import Image as Module
from PIL import ImageOps, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from PIL.Image import Image

from .parser import parser, get_var
from .objects import ImageRepr

def operation(p: list, operation: Callable, *args, **kwargs) -> None:
    image = get_var(p[1])
    image.image = operation(
        image.image,
        *args, **kwargs
    )

RT = TypeVar('RT')

def basic_operation(operation: Callable[[Image, ...], Image], *args, **kwargs) -> Callable[[Callable[[list], ...]], RT]:
    def decorator(func: Callable[[list], RT]) -> Callable[[list], RT]:
        @wraps(func)
        def inner(p: list) -> None:
            func(p)  # Just in case
            return operation(p, operation, *args, **kwargs)
        
        return inner
    return decorator
        
def basic_filter(filter: ImageFilter.Filter, *args, **kwargs) ->  Callable[[Callable[[list], ...]], ...]:
    return basic_operation(Image.filter, filter)
    
@parser.production('expr : INVERT variable')
@basic_operation(ImageOps.invert)
def invert_op(p: list) -> None:
    ...

@parser.production('expr : GRAYSCALE variable')
@basic_operation(ImageOps.grayscale)
def grayscale_op(p: list) -> None:
    ...

@parser.production('expr : MIRROR variable')
@basic_operation(ImageOps.mirror)
def mirror_op(p: list) -> None:
    ...

@parser.production('expr : FLIP variable')
@basic_operation(ImageOps.flip)
def flip_op(p: list) -> None:
    ...

@parser.production('expr : SOLARIZE variable')
@parser.production('expr : SOLARIZE variable number')
def solar_op(p: list) -> None:
    value = p[-1] if len(p) == 3 else 128
    return operation(p, ImageOps.solarize, value)

@parser.production('expr : POSTERIZE variable')
@parser.production('expr : POSTERIZE variable number')
def poster_op(p: list) -> None:
    value = p[-1] if len(p) == 3 else 4
    if value < 1 or value > 8:
        raise ValueError('Value must be an integer between 1 and 8')
    return operation(p, ImageOps.posterize, value)

@parser.production('expr : PAD variable ntuple')
@parser.production('expr : PAD variable ntuple color')
def pad_op(p: list) -> None:
    color = p[-1] if len(p) == 4 else None
    return operation(p, ImageOps.pad, size=p[2], color=color)

@parser.production('expr : SCALE variable number')
@parser.production('expr : SCALE variable number number')
def scale_op(p: list) -> None:
    resample = p[-1] if len(p) == 4 else 3
    return operation(p, ImageOps.scale, factor=p[2], resample=resample)

@parser.production('expr : EXPAND variable number')
@parser.production('expr : EXPAND variable number color')
def expand_op(p: list) -> None:
    fill = p[-1] if len(p) == 4 else 0
    return operation(p, ImageOps.expand, border=p[2], fill=fill)

@parser.production('expr : EQUALIZE variable')
@parser.production('expr : EQUALIZE variable MASK variable')
def equalize_op(p: list) -> None:
    mask = get_var(p[-1]) if len(p) == 4 else None
    return operation(p, ImageOps.equalize, mask=mask)

@parser.production('expr : FIT variable ntuple')
@parser.production('expr : FIT variable ntuple number')
def fit_op(p: list) -> None:
    bleed = p[-1] if len(p) == 4 else 3
    return operation(p, ImageOps.fit, size=p[2], bleed=bleed)

# filters

@parser.production('expr : EMBOSS variable')
@basic_filter(ImageFilter.EMBOSS)
def emboss(p: list) -> None:
    ...

@parser.production('expr : SMOOTH variable')
@basic_filter(ImageFilter.SMOOTH_MORE)
def smooth(p: list) -> None:
    ...

@parser.production('expr : SHARPEN variable')
@basic_filter(ImageFilter.SHARPEN)
def sharpen(p: list) -> None:
    ...

@parser.production('expr : DETAIL variable')
@basic_filter(ImageFilter.DETAIL)
def detail(p: list) -> None:
    ...

@parser.production('expr : CONTOUR variable')
@basic_filter(ImageFilter.CONTOUR)
def contour(p: list) -> None:
    ...

@parser.production('expr : EDGE_ENHANCE variable')
@basic_filter(ImageFilter.EDGE_ENHANCE_MORE)
def edge_enhance(p: list) -> None:
    ...

@parser.production('expr : BLUR variable')
@parser.production('expr : BLUR variable number')
def blur(p: list) -> None:
    radius = p[-1] if len(p) == 3 else 2
    return operation(p, Image.filter, ImageFilter.GaussianBlur(radius))

@parser.production('expr : MAX_FILTER variable')
@parser.production('expr : MAX_FILTER variable number')
def max_filter(p: list) -> None:
    deg = p[-1] if len(p) == 3 else 3
    return operation(p, Image.filter, ImageFilter.MaxFilter(deg))

@parser.production('expr : MIN_FILTER variable')
@parser.production('expr : MIN_FILTER variable number')
def min_filter(p: list) -> None:
    deg = p[-1] if len(p) == 3 else 3
    return operation(p, Image.filter, ImageFilter.MinFilter(deg))

@parser.production('expr : MODE_FILTER variable')
@parser.production('expr : MODE_FILTER variable number')
def mode_filter(p: list) -> None:
    deg = p[-1] if len(p) == 3 else 3
    return operation(p, Image.filter, ImageFilter.ModeFilter(deg))

@parser.production('expr : MEDIAN_FILTER variable')
@parser.production('expr : MEDIAN_FILTER variable number')
def median_filter(p: list) -> None:
    deg = p[-1] if len(p) == 3 else 3
    return operation(p, Image.filter, ImageFilter.MedianFilter(deg))

# ImageDraw operations

def draw(img: str, operation: str, *args, **kwargs) -> ImageDraw.Draw:
    img = get_var(img)
    cursor = ImageDraw.Draw(img.image)
    operation = getattr(cursor, operation)
    operation(*args, **kwargs)
    return cursor

@parser.production('font : FONT string')
@parser.production('font : FONT LEFT_PAREN string COMMA number RIGHT_PAREN')
def get_font(p: list) -> ImageFont.FreeTypeFont:
    if len(p) == 2:
        return ImageFont.truetype(p[1])
    else:
        return ImageFont.truetype(p[2], p[4])

@parser.production('expr : TEXT variable string ntuple')
@parser.production('expr : TEXT variable string ntuple font')
@parser.production('expr : TEXT variable string ntuple color')
@parser.production('expr : TEXT variable string ntuple font color')
def write_text(p: list) -> ImageDraw.Draw:
    coords, text = p[3], p[2]
    fill = p[-1] if len(p) > 4 and not isinstance(p, ImageFont.FreeTypeFont) else None
    font = p[4] if len(p) > 4 and isinstance(p[4], ImageFont.FreeTypeFont) else None
    return draw(p[1], 'multiline_text', xy=coords, text=text, fill=fill, font=font)


@parser.production('expr : LINE variable ntuple')
@parser.production('expr : LINE variable ntuple color')
def draw_line(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 4 else None
    return draw(p[1], 'line', xy=p[2], fill=fill)

@parser.production('expr : LINE variable ntuple number')
@parser.production('expr : LINE variable ntuple number color')
def draw_line_w(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 5 else None
    return draw(p[1], 'line', xy=p[2], fill=fill, width=p[3])


@parser.production('expr : ELLIPSE variable ntuple')
@parser.production('expr : ELLIPSE variable ntuple color')
def draw_ellipse(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 4 else None
    return draw(p[1], 'ellipse', xy=p[2], fill=fill)

@parser.production('expr : ELLIPSE variable ntuple number')
@parser.production('expr : ELLIPSE variable ntuple number color')
def draw_ellipse_w(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 5 else None
    return draw(p[1], 'ellipse', xy=p[2], fill=fill, width=p[3])


@parser.production('expr : DOT variable ntuple')
@parser.production('expr : DOT variable ntuple color')
def draw_dot(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 4 else None
    return draw(p[1], 'point', xy=p[2], fill=fill)


@parser.production('expr : ARC variable ntuple number COMMA number')
@parser.production('expr : ARC variable ntuple number COMMA number color')
def draw_arc(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 7 else None
    return draw(p[1], 'arc', xy=p[2], start=p[3], end=p[5], fill=fill)

@parser.production('expr : ARC variable ntuple number COMMA number number')
@parser.production('expr : ARC variable ntuple number COMMA number color number')
def draw_arc_w(p: list) -> ImageDraw.Draw:
    fill = p[-2] if len(p) == 8 else None
    return draw(p[1], 'arc', xy=p[2], start=p[3], end=p[5], fill=fill, width=p[-1])


@parser.production('expr : CHORD variable ntuple number COMMA number')
@parser.production('expr : CHORD variable ntuple number COMMA number color')
def draw_chord(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 7 else None
    return draw(p[1], 'chord', xy=p[2], start=p[3], end=p[5], fill=fill)

@parser.production('expr : CHORD variable ntuple number COMMA number number')
@parser.production('expr : CHORD variable ntuple number COMMA number color number')
def draw_chord_w(p: list) -> ImageDraw.Draw:
    fill = p[-2] if len(p) == 8 else None
    return draw(p[1], 'chord', xy=p[2], start=p[3], end=p[5], fill=fill, width=p[-1])


@parser.production('expr : POLYGON variable ntuple')
@parser.production('expr : POLYGON variable ntuple color')
def draw_polygon(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 4 else None
    return draw(p[1], 'polygon', xy=p[2], fill=fill)

@parser.production('expr : REGPOLYGON variable ntuple number')
@parser.production('expr : REGPOLYGON variable ntuple number color')
def draw_reg_polygon(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 5 else None
    return draw(p[1], 'regular_polygon', bounding_circle=p[2], n_sides=p[3], fill=fill)

@parser.production('expr : RECTANGLE variable ntuple')
@parser.production('expr : RECTANGLE variable ntuple color')
def draw_rec(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 4 else None
    return draw(p[1], 'rectangle', xy=p[2], fill=fill)

@parser.production('expr : RECTANGLE variable ntuple number')
@parser.production('expr : RECTANGLE variable ntuple number color')
def draw_rec_w(p: list) -> ImageDraw.Draw:
    fill = p[-1] if len(p) == 5 else None
    return draw(p[1], 'rectangle', xy=p[2], fill=fill, width=p[3])

# ImageEnhance operations

def enhance(p: list, operation: str) -> ImageEnhance._Enhance:
    img, degree = get_var(p[1]), p[-1]
    enhancer = getattr(ImageEnhance, operation)(img.image)
    img.image = enhancer.enhance(degree)
    return enhancer

@parser.production('expr : BRIGHTEN variable number')
def brighten(p: list) -> ImageEnhance.Brightness:
    return enhance(p, 'Brightness')

@parser.production('expr : CONTRAST variable number')
def contrast(p: list) -> ImageEnhance.Contrast:
    return enhance(p, 'Contrast')

@parser.production('expr : COLORIZE variable number')
def brighten(p: list) -> ImageEnhance.Color:
    return enhance(p, 'Color')

# ImageTransform operations

@parser.production('expr : DISTORT variable ntuple string ntuple')
@parser.production('expr : DISTORT variable ntuple string ntuple color')
def transform(p: list) -> int:
    img = get_var(p[1])
    fill = p[-1] if len(p) == 6 else None
    img.image = img.image.transform(p[2], method=getattr(Module, p[3].upper()), data=p[4], fillcolor=fill)
