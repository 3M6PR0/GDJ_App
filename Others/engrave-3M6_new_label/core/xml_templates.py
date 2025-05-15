import base64
from io import BytesIO
from PIL import Image
from numba import jit

__style1 = "font-size:2.0px;font-family:sans-serif;stroke-width:0.05"
__style2 = "font-size:3.5px;font-family:sans-serif;stroke-width:0.05"
__style3 = "font-size:2.0px;font-family:sans-serif;stroke-width:0.05;text-align:center;text-anchor:middle"
__style4 = "font-size:2.0px;font-family:sans-serif;stroke-width:0.05;text-align:left"
__style6 = "font-size:2.0px;font-family:sans-serif;stroke-width:0.05;text-align:left;text-anchor:left"
__style7 = "font-size:3.5px;font-family:sans-serif;stroke-width:0.05;text-anchor:middle;font-weight:bold"
__style8 = "fill:#000080;stroke:#000080;stroke-width:0.05"
__style9 = "fill:none;stroke:#ff0000;stroke-width:0.05"
__style_highlight = "fill:none;stroke:#00ff00;stroke-width:0.2;stroke-opacity:1"

### ___ COMMON ___ ###
def get_header(width: float, height: float, spacing=120, final=False):
    guidelines = ""
    for i in range(int((width%spacing)/2), int(width), spacing):
        guidelines += f"""<rect id="rectx" width="0.2" height="{height-4}" x="{i}" y="{2}" ry="0" style="fill:#0000FF;stroke:#0000FF;stroke-width:0.05"/>"""
    _result =  f"""
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg id="svg1" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" version="1.1"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns="http://www.w3.org/2000/svg">""" + ((f"""
    <rect id="rectmargin" width="{width-4}" height="{height-4}" x="2" y="2" ry="5.5" style="fill:none;stroke:#0000FF;stroke-width:0.5;stroke-opacity:1"/>
    <rect id="rectcanvas" width="{width}" height="{height}" x="0" y="0" ry="0" style="fill:none;stroke:#000000;stroke-width:0.5;stroke-opacity:1"/>
    """ + guidelines) if not final else "")
    return _result

def get_footer():
    return "</svg>"


### ___ LABEL CSA ___ ###
def get_csa_container(height: float, x=0, y=0, highlight=False):
    _highlighter = "" if not highlight else f""" <rect id="recthighlight" width="112" height="{height + 2}" x="{x}" y="{y}" ry="2.5" style="{__style_highlight}"/>"""
    return _highlighter + f"""
    <rect id="rectborder" width="110" height="{height}" x="{1 + x}" y="{1 + y}" ry="2.5" style="{__style9};stroke-opacity:1"/>
    <rect id="rect3" width="110" height="0.2" x="{1 + x}" y="{68 + y}" ry="0" style="{__style8}"/>
    <rect id="rect4" width="0.2" height="{height - 68}" x="{55 + x}" y="{68 + y}" ry="0" style="{__style8}"/>
    <rect id="rect5" width="105" height="0.2" x="{3 + x}" y="{74 + y}" ry="0" style="{__style8}"/>

    <text x="{4 + x}" y="{72 + y}" style="{__style1}">Circuit d'entrée / Input circuit</text>
    <text x="{36 + x}" y="{72 + y}" style="{__style1}">Volts</text>
    <text x="{46 + x}" y="{72 + y}" style="{__style1}">Amps</text>
    <text x="{58 + x}" y="{72 + y}" style="{__style1}">Circuit de sortie / Output circuit</text>
    <text x="{90 + x}" y="{72 + y}" style="{__style1}">Volts</text>
    <text x="{100 + x}" y="{72 + y}" style="{__style1}">Amps</text>
    """
def get_csa_fields(csa_code, volts, phases, hz, date, amps, temp, csa_type, nref, torque=False, x=0, y=0):
    _txt_torque = "In. Torque:" if torque else ""
    _val_torque = str(torque) + " Lb.in." if torque else ""
    return f"""
    <text x="{6+x}" y="{28+y}" style="{__style2}">CSA:</text>
    <text x="{6+x}" y="{32+y}" style="{__style2}">Volt:</text>
    <text x="{6+x}" y="{36+y}" style="{__style2}">Ph:</text>
    <text x="{6+x}" y="{40+y}" style="{__style2}">Hz:</text>
    <text x="{6+x}" y="{44+y}" style="{__style2}">Date:</text>

    <text x="{16+x}" y="{28+y}" style="{__style2}">{csa_code}</text>
    <text x="{16+x}" y="{32+y}" style="{__style2}">{volts} V</text>
    <text x="{16+x}" y="{36+y}" style="{__style2}">{phases}</text>
    <text x="{16+x}" y="{40+y}" style="{__style2}">{hz} Hz</text>
    <text x="{16+x}" y="{44+y}" style="{__style2}">{date}</text>

    <text x="{60+x}" y="{28+y}" style="{__style2}">{_txt_torque}</text>
    <text x="{60+x}" y="{32+y}" style="{__style2}">Amps:</text>
    <text x="{60+x}" y="{36+y}" style="{__style2}">Temp:</text>
    <text x="{60+x}" y="{40+y}" style="{__style2}">Type:</text>
    <text x="{60+x}" y="{44+y}" style="{__style2}">No. Ref:</text>

    <text x="{80+x}" y="{28+y}" style="{__style2}">{_val_torque}</text>
    <text x="{80+x}" y="{32+y}" style="{__style2}">{amps} A</text>
    <text x="{80+x}" y="{36+y}" style="{__style2}">{temp}</text>
    <text x="{80+x}" y="{40+y}" style="{__style2}">{csa_type}</text>
    <text x="{80+x}" y="{44+y}" style="{__style2}">{nref}</text>
    """
def get_csa_cus(x=0, y=0):
    return f"""
    <text x="{87+x}" y="{21+y}" style="{__style2};fill-opacity:1;">C</text>
    <text x="{102+x}" y="{21+y}" style="{__style2};fill-opacity:1;">US</text>
    """
def get_csa_scr(volts, scr, x=0, y=0):
    return f"""
    <text x="{55+x}" y="{50+y}" style="{__style3}">Convient a un circuit pouvant débiter un courant de défaut maximal de {scr} KA efficaces</text>
    <text x="{55+x}" y="{52.5+y}" style="{__style3}">symétriques sous une tension maximale de {volts} V au maximum.</text>
    <text x="{55+x}" y="{57+y}" style="{__style3}">Suitable for use on a circuit capable of delivering not more than {scr} KA RMS symetrical amperes</text>
    <text x="{55+x}" y="{59.5+y}" style="{__style3}">at {volts} V maximum.</text>
    <text x="{55+x}" y="{65+y}" style="{__style3};font-weight:bold;">Panneau industriel de commande / Industrial control panel</text>
    """
def get_csa_input_circuit(name: str, volts: str, amps: str, h, x=0, y=0):
    return f"""
    <text x="{4+x}" y="{h+y}" style="{__style1}">{name}</text>
    <text x="{36+x}" y="{h+y}" style="{__style1}">{volts}</text>
    <text x="{46+x}" y="{h+y}" style="{__style1}">{amps}</text>
    """
def get_csa_output_circuit(name: str, volts: str, amps: str, h, x=0, y=0):
    return f"""
    <text x="{58+x}" y="{h+y}" style="{__style1}">{name}</text>
    <text x="{90+x}" y="{h+y}" style="{__style1}">{volts}</text>
    <text x="{100+x}" y="{h+y}" style="{__style1}">{amps}</text>
    """


### ___ LABEL FUSE ___ ###
def get_fuse_container(height: float, x=0, y=0, highlight=False):
    _highlighter = "" if not highlight else f""" <rect id="recthighlight" width="112" height="{height+2}" x="{x}" y="{y}" ry="2.5" style="{__style_highlight}"/>"""
    return _highlighter + f"""
    <text x="{41 + x}" y="{6.5 + y}" style="font-size:3.5px;font-family:sans-serif;stroke-width:0.05;font-weight:bold">
        FUSIBLES / FUSES
    </text>
    <rect id="fuse_border" width="110" height="{height}" x="{1 + x}" y="{1 + y}" ry="2.5" style="{__style9}"/>
    <rect id="rectline1" width="110" height="0.2" x="{1 + x}" y="{10 + y}" style="{__style8}"/>
    <rect id="rectline2" width="110" height="0.2" x="{1 + x}" y="{15 + y}" style="{__style8}"/>
    <rect id="rectline3" width="110" height="0.2" x="{1 + x}" y="{height - 22 + y}" style="{__style8}"/>
    <text x="{4 + x}" y="{13 + y}" style="{__style4}">Étiquette</text>
    <text x="{25 + x}" y="{13 + y}" style="{__style4}">Description technique</text>
    <text x="{90 + x}" y="{13 + y}" style="{__style4}">Numéro de pièce</text>
    <text x="{60 + x}" y="{height - 16 + y}" style="{__style7}">LES FUSIBLES DE REMPLACEMENT DOIVENT ÊTRE</text>
    <text x="{60 + x}" y="{height - 12 + y}" style="{__style7}">DE MÊME TYPE ET DE MÊME CAPACITÉ</text>
    <text x="{58 + x}" y="{height - 8 + y}" style="{__style7}">NOMINALE QUE LES FUSIBLES D'ORIGINE</text>
    <text x="{58 + x}" y="{height - 2 + y}" style="{__style7}">REPLACE FUSES WITH SAME TYPE AND RATING</text>
    """
def get_fuse_line(tag: str, desc: str, part: str, n: float, x=0, y=0):
    return f"""
    <text x="{4+x}" y="{n+y}" style="{__style6}">- {tag}</text>
    <text x="{25+x}" y="{n+y}" style="{__style6}">{desc}</text>
    <text x="{90+x}" y="{n+y}" style="{__style6}">{part}</text>
    """


### ___ LABEL CURRENT ___ ###
def get_current_label(height: float, amps=1, volts=120, x=0, y=0, highlight=False):
    _highlighter = "" if not highlight else f""" <rect id="recthighlight" width="112" height="{height+2}" x="{x}" y="{y}" ry="2.5" style="{__style_highlight}"/>"""
    return _highlighter + f"""
    <rect id="fuse_border" width="110" height="{height}" x="{x+1}" y="{y+1}" ry="2.5" style="{__style9}" />
    <rect id="rectline1" width="110" height="0.2" x="{x+1}" y="{8.0+y}" style="{__style8}" />
    <rect id="rectline3" width="110" height="0.2" x="{x+1}" y="{24.0+y}" style="{__style8}" />
    <text x="{42 + x}" y="{6+y}" style="font-weight:bold;font-size:5px;font-family:sans-serif;stroke-width:0.05" id="text1">ATTENTION</text>
    <text x="{56 + x}" y="{13.0 + y}" style="{__style7}">CONVIENT À L'UTILISATION DANS UN CIRCUIT CAPABLE DE</text>
    <text x="{56 + x}" y="{17.5 + y}" style="{__style7}">LIVRER UN COURANT RMS SYMÉTRIQUE</text>
    <text x="{56 + x}" y="{22.0 + y}" style="{__style7}">D'AU PLUS {amps} A, À UNE TENSION MAXIMALE DE {volts} V</text>
    <text x="{56 + x}" y="{28.5 + y}" style="{__style7}">SUITABLE FOR USE ON A CIRCUIT CAPABLE OF DELIVERING</text>
    <text x="{56 + x}" y="{33.0 + y}" style="{__style7}">NOT MORE THAN {amps} RMS SYMMETRICAL</text>
    <text x="{56 + x}" y="{37.5 + y}" style="{__style7}">AMPERES WITH {volts} V MAXIMUM</text>
    """


### ___ LABEL JACMAR ___ ###
def get_jacmar_container(height: float, width: float = 110, x=0, y=0, highlight=False):
    _highlighter = "" if not highlight else f""" <rect id="recthighlight" width="{width+2}" height="{height+2}" x="{x}" y="{y}" ry="2.5" style="{__style_highlight}"/>"""
    return _highlighter + f"""
    <rect id="jacmar_border" width="{width}" height="{height}" x="{1 + x}" y="{1 + y}" ry="2.5" style="{__style9};stroke-opacity:1"/>
    """

def get_jacmar_fields(date_str, nref_str, x=0, y=0):
    # Ajustement des positions x pour un meilleur espacement horizontal
    date_value_x_offset = 18
    nref_label_x_offset = 55  
    nref_value_x_offset = 72 
    return f"""
    <text x="{6+x}" y="{y}" style="{__style2}">Date:</text>
    <text x="{date_value_x_offset+x}" y="{y}" style="{__style2}">{date_str}</text>

    <text x="{nref_label_x_offset+x}" y="{y}" style="{__style2}">No. Ref:</text>
    <text x="{nref_value_x_offset+x}" y="{y}" style="{__style2}">{nref_str}</text>
    """


### ___ IMAGES ___ ###
class SVGImage:
    __loaded_images = []
    @staticmethod
    def get(path):
        for img in SVGImage.__loaded_images:
            if img.path == path:
                return img
        new_img = SVGImage(path)
        SVGImage.__loaded_images.append(new_img)
        return new_img

    def __init__(self, path):
        self.path = path
        self.format = path[-3:]
        with Image.open(path) as img:
            self.width = img.width
            self.height = img.height
            buffered = BytesIO()
            if self.format.upper() == "JPG":
                self.format = "jpeg"
            img.save(buffered, format=self.format.upper())
            self.img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    def get_href(self, x, y, scaling):
        w = self.width * scaling
        h = self.height * scaling
        return f"""
        <image id="imported_image" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" style="image-rendering:optimizeQuality"
        xlink:href="data:image/{self.format.lower()};base64,{self.img_base64}&#10;"/>
        """

    def get_href_autoscale(self, x, y, dx_max=80, dy_max=22, stick="W"):
        scaling = 1/max(self.width/dx_max, self.height/dy_max)
        w = self.width * scaling
        h = self.height * scaling
        xp = x + (0 if "W" in stick else (dx_max-w if "E" in stick else (dx_max-w)/2))
        yp = y + (0 if "N" in stick else (dy_max-h if "S" in stick else (dy_max-h)/2))
        return f"""
        <image id="imported_image" x="{xp}" y="{yp}" width="{w}" height="{h}" preserveAspectRatio="none" style="image-rendering:optimizeQuality" 
        xlink:href="data:image/{self.format.lower()};base64,{self.img_base64}&#10;"/>
        """

def get_logo_company(image_path, x=0.0, y=0.0):
    return SVGImage.get(image_path).get_href_autoscale(x, y)

def get_logo_csa(path, x=0.0, y=0.0):
    return SVGImage.get(path).get_href(x+88, y+4.75, 0.085)
