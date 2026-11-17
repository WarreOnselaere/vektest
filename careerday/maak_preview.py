import sys, ezdxf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy
out = sys.argv[2]
for name in ezdxf.readfile(sys.argv[1]).layout_names():
    if name == "Model": continue
    doc = ezdxf.readfile(sys.argv[1])
    lay = doc.layouts.get(name)
    vp = [e for e in lay if e.dxftype()=="VIEWPORT" and e.dxf.id>1][0]
    for ln in vp.frozen_layers: doc.layers.get(ln).off()
    for l in doc.layers:
        ov = l.get_vp_overrides()
        if ov.has_overrides(vp.dxf.handle): l.color = ov.get_color(vp.dxf.handle)
    fig = plt.figure(figsize=(841/25.4, 594/25.4))
    ax = fig.add_axes([0,0,1,1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR, lineweight_scaling=1.0)
    ctx = RenderContext(doc); ctx.set_current_layout(lay)
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(lay, finalize=True)
    ax.set_xlim(0,841); ax.set_ylim(0,594)
    fn = f"{out}/{name.replace(' ','_')}"
    fig.savefig(fn+".pdf"); fig.savefig(fn+".png", dpi=150)
    plt.close(fig); print(fn)
