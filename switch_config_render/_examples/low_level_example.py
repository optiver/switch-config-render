import svgwrite
from switch_config_render.generate_svg import FrontPanelPorts, FPGAPorts, Canvas

# Vertices of the shapes used to represent FPGA applications
def get_hexagon_points():
    return [(0, 1.5), (1, 3), (3, 3), (4, 1.5), (3, 0), (1, 0), (0, 1.5)]


def get_mux_points():
    return [(1, 0), (0, 2), (4, 2), (3, 0), (1, 0)]


shapes = {"custom": get_hexagon_points(), "mux": get_mux_points()}


def render_low_level_example():
    COLLECTION_SPACING = 100
    LEGEND_WIDTH = 400

    # Create a front panel box with three interfaces
    fpp = FrontPanelPorts(3)

    # Create one FPGA box called "central_fpga" with 8 ap interfaces
    fpgas = {
        "central_fpga": FPGAPorts(
            "central_fpga", ["ap" + str(i) for i in range(1, 9)], {}, shapes, []
        )
    }

    # Determine the width of all the FPGA boxes
    fpgas_width = COLLECTION_SPACING
    for fpga_box in fpgas.values():
        fpgas_width += fpga_box.width + COLLECTION_SPACING

    # Center the boxes with respect to each other
    fpp_x = COLLECTION_SPACING
    if fpp.width < fpgas_width:
        fpp_x = COLLECTION_SPACING + (fpgas_width / 2.0) - (fpp.width / 2.0)

    fpgas_x = COLLECTION_SPACING
    if fpp.width > fpgas_width:
        fpgas_x = COLLECTION_SPACING + (fpp.width / 2.0) - (fpgas_width / 2.0)

    boxes_width = max(fpgas_width, fpp.width + 2 * COLLECTION_SPACING)
    drawing_width = boxes_width + LEGEND_WIDTH

    # The SVG resolution is 10pts per millimeter
    drawing = svgwrite.Drawing(
        filename="low_level_example.svg",
        debug=True,
        size=("{}mm".format(str(drawing_width / 10)), "180mm"),
        viewBox=("0 0 {} 1800".format(drawing_width)),
    )
    canvas = Canvas(drawing)

    # Render the front panel interfaces box and all its interfaces
    fpp.render_box(canvas, fpp_x, COLLECTION_SPACING)
    fpp.render_next_interface(
        canvas, "et1", {"alias": "exec_0", "description": "Execution port 0"}
    )
    fpp.render_next_interface(
        canvas, "et2", {"alias": "exec_1", "description": "Execution port 1"}
    )
    fpp.render_next_interface(
        canvas, "et3", {"alias": "exec_2", "description": "Execution port 2"}
    )

    # Render the application interfaces box and all its application interfaces
    fpgas["central_fpga"].render_box(canvas, fpgas_x, 1000)
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap1", {"alias": "exec_0", "description": "Execution port 0"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap2", {"alias": "exec_1", "description": "Execution port 1"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap3", {"alias": "exec_2", "description": "Execution port 2"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap4", {"alias": "exec_3", "description": "Execution port 3"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap5", {"alias": "exec_4", "description": "Execution port 4"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap6", {"alias": "exec_5", "description": "Execution port 5"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap7", {"alias": "exec_6", "description": "Execution port 6"}
    )
    fpgas["central_fpga"].render_next_interface(
        canvas, "ap8", {"alias": "exec_7", "description": "Execution port 7"}
    )
    fpgas["central_fpga"].draw_app(canvas, "dev_0", "custom", 80, ["ap1", "ap2", "ap3"])
    fpgas["central_fpga"].draw_app(
        canvas, "mux_0", "mux", 80, ["ap4", "ap5", "ap6", "ap7"]
    )

    fpgas["central_fpga"].draw_apps_connections(canvas)
    fpgas["central_fpga"].draw_apps_connections(canvas)

    # Render the connections
    canvas.render_connection("et1", "ap1", bidir=False, onchip=False, types=("abc",))
    canvas.render_connection(
        "ap8", "ap1", bidir=True, onchip=False, types=("abc", "def")
    )

    # Render the legend
    canvas.render_legend(boxes_width, COLLECTION_SPACING, LEGEND_WIDTH)

    # Save to file
    canvas.drawing.save()
