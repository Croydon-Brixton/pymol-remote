from pymol_remote.client import PymolSession


def make_pymol_pretty(session: PymolSession) -> None:
    """
    Make PyMOL look pretty with settings inspired from:
        - https://gist.github.com/kate-fie/50a749e03e81d15c320f0306150d6f66

    Checking out her blog post (https://www.blopig.com/blog/2024/12/making-pretty-pictures-in-pymol-v2/)
    is highly recommended.
    """
    # Bondi VDW values
    bondi_vdw = {
        "Ac": 2.00,
        "Al": 2.00,
        "Am": 2.00,
        "Sb": 2.00,
        "Ar": 1.88,
        "As": 1.85,
        "At": 2.00,
        "Ba": 2.00,
        "Bk": 2.00,
        "Be": 2.00,
        "Bi": 2.00,
        "Bh": 2.00,
        "B": 2.00,
        "Br": 1.85,
        "Cd": 1.58,
        "Cs": 2.00,
        "Ca": 2.00,
        "Cf": 2.00,
        "C": 1.70,
        "Ce": 2.00,
        "Cl": 1.75,
        "Cr": 2.00,
        "Co": 2.00,
        "Cu": 1.40,
        "Cm": 2.00,
        "Ds": 2.00,
        "Db": 2.00,
        "Dy": 2.00,
        "Es": 2.00,
        "Er": 2.00,
        "Eu": 2.00,
        "Fm": 2.00,
        "F": 1.47,
        "Fr": 2.00,
        "Gd": 2.00,
        "Ga": 1.87,
        "Ge": 2.00,
        "Au": 1.66,
        "Hf": 2.00,
        "Hs": 2.00,
        "He": 1.40,
        "Ho": 2.00,
        "In": 1.93,
        "I": 1.98,
        "Ir": 2.00,
        "Fe": 2.00,
        "Kr": 2.02,
        "La": 2.00,
        "Lr": 2.00,
        "Pb": 2.02,
        "Li": 1.82,
        "Lu": 2.00,
        "Mg": 1.73,
        "Mn": 2.00,
        "Mt": 2.00,
        "Md": 2.00,
        "Hg": 1.55,
        "Mo": 2.00,
        "Nd": 2.00,
        "Ne": 1.54,
        "Np": 2.00,
        "Ni": 1.63,
        "Nb": 2.00,
        "N": 1.55,
        "No": 2.00,
        "Os": 2.00,
        "O": 1.52,
        "Pd": 1.63,
        "P": 1.80,
        "Pt": 1.72,
        "Pu": 2.00,
        "Po": 2.00,
        "K": 2.75,
        "Pr": 2.00,
        "Pm": 2.00,
        "Pa": 2.00,
        "Ra": 2.00,
        "Rn": 2.00,
        "Re": 2.00,
        "Rh": 2.00,
        "Rb": 2.00,
        "Ru": 2.00,
        "Rf": 2.00,
        "Sm": 2.00,
        "Sc": 2.00,
        "Sg": 2.00,
        "Se": 1.90,
        "Si": 2.10,
        "Ag": 1.72,
        "Na": 2.27,
        "Sr": 2.00,
        "S": 1.80,
        "Ta": 2.00,
        "Tc": 2.00,
        "Te": 2.06,
        "Tb": 2.00,
        "Tl": 1.96,
        "Th": 2.00,
        "Tm": 2.00,
        "Sn": 2.17,
        "Ti": 2.00,
        "W": 2.00,
        "U": 1.86,
        "V": 2.00,
        "Xe": 2.16,
        "Yb": 2.00,
        "Y": 2.00,
        "Zn": 1.39,
        "Zr": 2.00,
    }

    for element, vdw in bondi_vdw.items():
        session.alter(f"elem {element}", f"vdw={vdw:.2f}")

    session.rebuild()

    # GitHub: matteoferla color palette
    color_palette = {
        "turquoise": [0.18823529411764706, 0.8352941176470589, 0.7843137254901961],
        "coral": [1.0, 0.4980392156862745, 0.3137254901960784],
        "teal": [0.0, 0.5019607843137255, 0.5019607843137255],
        "sage": [0.6980392156862745, 0.6745098039215687, 0.5333333333333333],
        "lavender": [0.9019607843137255, 0.9019607843137255, 0.9803921568627451],
        "mustard": [1.0, 0.8588235294117647, 0.34509803921568627],
        "aquamarine": [0.4980392156862745, 1.0, 0.8313725490196079],
        "feijoa": [0.6470588235294118, 0.8431372549019608, 0.5215686274509804],
        "rose": [1.0, 0.0, 0.4980392156862745],
        "paleturquoise": [0.6862745098039216, 0.9333333333333333, 0.9333333333333333],
        "lightcoral": [0.9411764705882353, 0.5019607843137255, 0.5019607843137255],
        "lightpurple": [0.8117647058823529, 0.6235294117647059, 1.0],
        "lightblue": [0.5294117647058824, 0.807843137254902, 0.9803921568627451],
        "lightgreen": [0.5647058823529412, 0.9333333333333333, 0.5647058823529412],
        "lightyellow": [1.0, 1.0, 0.8784313725490196],
        "lightorange": [1.0, 0.6274509803921569, 0.47843137254901963],
        "lightpink": [1.0, 0.7137254901960784, 0.7568627450980392],
        "robinsegg": [0.0, 0.8, 0.8],
        "cerulean": [0.0, 0.4823529411764706, 0.6549019607843137],
        "periwinkle": [0.8, 0.8, 1.0],
    }

    for color_name, rgb in color_palette.items():
        session.set_color(color_name, rgb)

    # Custom color palette
    custom_colors = {
        "canary": [251 / 255, 248 / 255, 204 / 255],
        "orangecream": [253 / 255, 228 / 255, 207 / 255],
        "peach": [255 / 255, 207 / 255, 210 / 255],
        "lightpurple": [241 / 255, 192 / 255, 232 / 255],
        "purple": [207 / 255, 186 / 255, 240 / 255],
        "purpleblue": [163 / 255, 196 / 255, 243 / 255],
        "blue": [144 / 255, 219 / 255, 244 / 255],
        "lightblue": [142 / 255, 236 / 255, 245 / 255],
        "marine": [152 / 255, 245 / 255, 225 / 255],
        "green": [185 / 255, 251 / 255, 192 / 255],
    }

    for color_name, rgb in custom_colors.items():
        session.set_color(color_name, rgb)

    # Workspace settings
    session.bg_color("grey19")
    session.set("ray_opaque_background", "off")
    session.set("orthoscopic", 0)
    session.set("transparency", 0.5)
    session.set("dash_gap", 0)
    session.set("ray_trace_mode", 1)
    session.set("ray_trace_color", "black")
    session.set("antialias", 3)
    session.set("ambient", 0.5)
    session.set("direct", 0.45)
    session.set("spec_count", 5)
    session.set("shininess", 50)
    session.set("specular", 0)
    session.set("reflect", 0.1)
    session.space("cmyk")
    session.rebuild()
