
import copy
import svgwrite

from switch_config_render.utils import (
    get_sorted_itfs,
    get_average_itf_idx,
    get_connection_types,
)
from switch_config_render.canvas import Canvas

_INTERFACE_WIDTH = 200
_INTERFACE_HEIGHT = 150
_INTERFACE_H_CLEARANCE = 30
_INTERFACE_V_CLEARANCE = 50
_INTERFACE_SPACE = _INTERFACE_WIDTH + 2 * _INTERFACE_H_CLEARANCE
_COLLECTION_SPACING = 100
_LEGEND_WIDTH = 400


class InterfaceCollection(object):
    def __init__(self, id, interface_count, front_panel, height):
        self.id = id
        self.name = id.replace("_", " ").title()
        self.front_panel = front_panel
        self.width = interface_count * _INTERFACE_SPACE
        self.height = height
        self.x = None
        self.y = None
        self.itf_idx = 0

    def render_box(self, canvas, x, y):
        box = canvas.drawing.add(canvas.drawing.g(id="box_" + self.id, fill="white"))
        box.add(
            canvas.drawing.rect(
                insert=(x, y),
                size=(self.width, self.height),
                stroke="black",
                stroke_width=6,
            )
        )

        if self.front_panel:
            box.add(
                canvas.drawing.text(
                    self.name,
                    insert=(x + self.width / 2.0, y + 50),
                    alignment_baseline="middle",
                    text_anchor="middle",
                    fill="black",
                    style="font-family:Courier New",
                    font_size=30,
                )
            )
        else:
            box.add(
                canvas.drawing.text(
                    self.name,
                    insert=(x + self.width / 2.0, y + self.height - 20),
                    alignment_baseline="middle",
                    text_anchor="middle",
                    fill="black",
                    style="font-family:Courier New",
                    font_size=30,
                )
            )

        self.x = x
        self.y = y

    def render_next_interface(self, canvas, itf, params):
        x = self.x + (self.itf_idx * _INTERFACE_SPACE)
        y = self.y
        if self.front_panel:
            y += 50

        middle_x = x + _INTERFACE_H_CLEARANCE + _INTERFACE_WIDTH / 2

        shapes = canvas.drawing.add(canvas.drawing.g(id=itf, fill="white"))

        shapes.add(
            canvas.drawing.rect(
                insert=(x + _INTERFACE_H_CLEARANCE, y + _INTERFACE_V_CLEARANCE),
                size=(_INTERFACE_WIDTH, _INTERFACE_HEIGHT),
                stroke="black",
                stroke_width=5,
            )
        )

        # Calculate the connection points for this interface
        lower_mid = (middle_x, y + _INTERFACE_V_CLEARANCE + _INTERFACE_HEIGHT)
        upper_mid = (middle_x, y + _INTERFACE_V_CLEARANCE)

        canvas.add_interface_connection_points(
            itf, self.front_panel, lower_mid, upper_mid
        )

        # Make the front panel interface ports look like RJ-45 connectors
        if self.front_panel:
            small_box_w = 50
            small_box_h = 40
            small_box_y = y + _INTERFACE_HEIGHT + _INTERFACE_V_CLEARANCE - small_box_h
            shapes.add(
                canvas.drawing.rect(
                    insert=((x + _INTERFACE_H_CLEARANCE), small_box_y),
                    size=(small_box_w, small_box_h),
                    stroke="black",
                    stroke_width=4,
                )
            )
            shapes.add(
                canvas.drawing.rect(
                    insert=(
                        (x + _INTERFACE_WIDTH + _INTERFACE_H_CLEARANCE - small_box_w),
                        small_box_y,
                    ),
                    size=(small_box_w, small_box_h),
                    stroke="black",
                    stroke_width=4,
                )
            )

        shapes.add(
            canvas.drawing.text(
                itf,
                insert=(middle_x, y + 120),
                alignment_baseline="middle",
                text_anchor="middle",
                fill="black",
                font_size=50,
            )
        )

        descs = canvas.drawing.add(canvas.drawing.g(id=itf + "_desc", fill="black"))

        if "alias" in params:
            alias = "({})".format(params["alias"])
            descs.add(
                canvas.drawing.text(
                    alias,
                    insert=(middle_x, y + 150),
                    alignment_baseline="middle",
                    text_anchor="middle",
                    style="font-family:Courier New",
                    font_size=15,
                )
            )

        if "description" in params:
            desc = params["description"]
            if self.front_panel:
                descs.add(
                    canvas.drawing.text(
                        desc,
                        insert=(middle_x, y + 40),
                        alignment_baseline="middle",
                        text_anchor="middle",
                        style="font-family:Courier New",
                        font_size=15,
                    )
                )
            else:
                descs.add(
                    canvas.drawing.text(
                        desc,
                        insert=(middle_x, y + 180),
                        alignment_baseline="middle",
                        text_anchor="middle",
                        style="font-family:Courier New",
                        font_size=15,
                    )
                )

        self.itf_idx += 1


class FrontPanelPorts(InterfaceCollection):
    def __init__(self, interface_count):
        super(FrontPanelPorts, self).__init__(
            "front_panel_interfaces", interface_count, True, 300
        )


class FPGAPorts(InterfaceCollection):
    DEVICE_Y_OFFSET = 400

    def __init__(self, id, interface_count):
        super(FPGAPorts, self).__init__(id, interface_count, False, 750)

    def draw_device(self, canvas, name, points, size_factor, ports):
        device = canvas.drawing.add(
            canvas.drawing.g(
                id="device_" + self.id + "_" + name, fill="white", font_size=50
            )
        )

        width = max([x for x, _ in points]) * size_factor
        height = max([y for _, y in points]) * size_factor

        # Determine the placement of the device by selecting the mid-point of all the connected ports
        itf_coords = [
            canvas.app_itf_coords[itf] for itf in ports if itf in canvas.app_itf_coords
        ]
        itf_x_coords = [x for x, _ in itf_coords]

        x_offset = min(itf_x_coords) + (max(itf_x_coords) - min(itf_x_coords)) / 2.0
        x_offset -= width / 2.0

        abs_points = [
            (
                x * size_factor + x_offset,
                y * size_factor + self.y + FPGAPorts.DEVICE_Y_OFFSET,
            )
            for x, y in points
        ]

        path = ["M{},{}".format(*abs_points[0])] + [
            "L{},{}".format(*point) for point in abs_points[1:]
        ]
        device.add(
            canvas.drawing.path(path, fill="none", stroke_width=6, stroke="black")
        )

        x_middle = x_offset + width / 2.0
        y_middle = self.y + FPGAPorts.DEVICE_Y_OFFSET + height / 2.0
        device.add(
            canvas.drawing.text(
                name,
                insert=(x_middle, y_middle),
                alignment_baseline="middle",
                text_anchor="middle",
                fill="black",
                stroke_width=1,
            )
        )

        device_conn_coords = (x_middle, (self.y + FPGAPorts.DEVICE_Y_OFFSET))
        for port in ports:
            device.add(
                canvas.drawing.line(
                    device_conn_coords,
                    canvas.app_itf_coords[port],
                    stroke_width=4,
                    stroke="black",
                )
            )


def generate_system_svg(
    filename,
    interfaces,
    connections,
    fpga_devices,
    device_shapes,
    dominant_type=None,
):
    fpp = FrontPanelPorts(len(get_sorted_itfs(interfaces, "et")))

    fpga_ids = []
    fpgas = {}
    for fpga_id, devices in fpga_devices.items():
        ap_interfaces = sum([device["ports"] for device in devices.values()], [])
        fpgas[fpga_id] = FPGAPorts(fpga_id, len(ap_interfaces))

        avg_itf = get_average_itf_idx(ap_interfaces, "ap")
        fpga_ids.append((fpga_id, avg_itf))

    fpga_ids = [fpga_id for fpga_id, _ in sorted(fpga_ids, key=lambda info: info[1])]

    fpgas_width = _COLLECTION_SPACING
    fpgas_height = 0
    for fpga_box in fpgas.values():
        fpgas_width += fpga_box.width + _COLLECTION_SPACING
        fpgas_height = max(fpgas_height, fpga_box.height)

    # Center the boxes with respect to each other
    fpp_x = _COLLECTION_SPACING
    if fpp.width < fpgas_width:
        fpp_x = _COLLECTION_SPACING + (fpgas_width / 2.0) - (fpp.width / 2.0)

    fpgas_x = _COLLECTION_SPACING
    if fpp.width > fpgas_width:
        fpgas_x = _COLLECTION_SPACING + (fpp.width / 2.0) - (fpgas_width / 2.0)

    boxes_width = max(fpgas_width, fpp.width + 2 * _COLLECTION_SPACING)
    drawing_width = boxes_width + _LEGEND_WIDTH
    drawing_height = fpp.height + _COLLECTION_SPACING / 2

    if fpgas_height > 0:
        fpgas_y = drawing_height + _COLLECTION_SPACING + 400 + len(connections) * 20
        drawing_height = fpgas_y + fpgas_height + _COLLECTION_SPACING / 2

    drawing = svgwrite.Drawing(
        filename=filename,
        debug=True,
        size=(
            "{}mm".format(str(drawing_width / 10)),
            "{}mm".format(str(drawing_height / 10)),
        ),
        viewBox=("0 0 {} {}".format(drawing_width, drawing_height)),
        fill="white",
    )

    drawing.add(
        drawing.rect(
            insert=(0, 0), size=("100%", "100%"), rx=None, ry=None, fill="white"
        )
    )
    canvas = Canvas(drawing)

    # Render all the front panel interfaces
    fpp.render_box(canvas, fpp_x, _COLLECTION_SPACING / 2.0)
    for itf in get_sorted_itfs(interfaces, "et"):
        fpp.render_next_interface(canvas, itf, interfaces[itf])

    # Render all the FPGAs, their interfaces and their devices
    for fpga_id in fpga_ids:
        fpgas[fpga_id].render_box(canvas, fpgas_x, fpgas_y)

        sorted_devices = []
        for device, params in fpga_devices[fpga_id].items():
            avg_itf = get_average_itf_idx(params["ports"], "ap")
            sorted_devices.append((device, avg_itf))
        sorted_devices = [
            device for device, _ in sorted(sorted_devices, key=lambda info: info[1])
        ]

        for device in sorted_devices:
            params = fpga_devices[fpga_id][device]
            for itf in get_sorted_itfs(params["ports"], "ap"):
                fpgas[fpga_id].render_next_interface(canvas, itf, interfaces[itf])

            fpgas[fpga_id].draw_device(
                canvas, device, device_shapes[params["type"]], 80, params["ports"]
            )

        fpgas_x += fpgas[fpga_id].width + _COLLECTION_SPACING

    # Render the connections
    singledir_connections = copy.deepcopy(connections)
    bidir_connections = {}
    for dst, src in connections.items():
        if src in singledir_connections and singledir_connections[src] == dst:
            bidir_connections[dst] = src
            del singledir_connections[dst]
            del singledir_connections[src]

    for endp1, endp2 in bidir_connections.items():
        canvas.render_connection(
            endp1,
            endp2,
            bidir=True,
            types=get_connection_types(
                interfaces, endp1, endp2, bidir=True, dominant_type=dominant_type
            ),
        )

    for dst, src in singledir_connections.items():
        canvas.render_connection(
            dst,
            src,
            bidir=False,
            types=get_connection_types(
                interfaces, dst, src, bidir=False, dominant_type=dominant_type
            ),
        )

    canvas.render_legend(boxes_width, _COLLECTION_SPACING, _LEGEND_WIDTH)
    canvas.drawing.save()
