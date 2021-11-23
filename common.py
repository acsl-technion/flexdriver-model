import plotnine as p9
import mizani

fig_width = 3.37566 # in
fig_star_width = 7.00137 # in
fig_height = 2 # in

performance_model_height = 1.3 # in

p9.options.current_theme = p9.theme_bw(base_size=7)

top_legend = [
    p9.theme(legend_position=(0.5,1),
             legend_direction='horizontal',
             legend_title=p9.element_blank(),
             legend_box_margin=0.1,
             legend_box='horizontal',
            ),
]

pal = mizani.palettes.brewer_pal("qual", "Set2")
software_color, fld_color, fpga_color = pal(3)

eth_pci = mizani.palettes.brewer_pal("qual", "Set1")(2)
eth_pci_scale = p9.scale_color_manual(values=eth_pci)
local_remote_scale=p9.scale_color_manual(values=list(reversed(eth_pci)))