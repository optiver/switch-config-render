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
_INTERFACE_H_END_CLEARANCE = 80
_INTERFACE_V_CLEARANCE = 50
_INTERFACE_SPACE = _INTERFACE_WIDTH + 2 * _INTERFACE_H_CLEARANCE
_COLLECTION_SPACING = 100
_LEGEND_WIDTH = 400
_ONCHIP_CONNECTION_CLEARANCE = 50


class InterfaceCollection(object):
    def __init__(self, id, interface_count, num_portless_apps, front_panel, height):
        self.id = id
        self.name = id.replace("_", " ").title()
        self.front_panel = front_panel
        self.width = (interface_count + num_portless_apps) * _INTERFACE_SPACE + 2 * _INTERFACE_H_END_CLEARANCE
        self.height = height
        self.x = None
        self.y = None
        self.itf_idx = 0
        self.itf_params = {}

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
                    style="font-family:monospace",
                    font_size=30,
                )
            )
        else:
            box.add(
                canvas.drawing.text(
                    self.name,
                    insert=(x + 20, y + self.height - 20),
                    fill="black",
                    style="font-family:monospace",
                    font_size=30,
                )
            )

        self.x = x
        self.y = y

    def get_current_x(self):
        return self.x + (self.itf_idx * _INTERFACE_SPACE)\
            + _INTERFACE_H_END_CLEARANCE + _INTERFACE_H_CLEARANCE + _INTERFACE_WIDTH / 2

    def render_next_interface(self, canvas, itf, params):
        x = self.x + (self.itf_idx * _INTERFACE_SPACE) + _INTERFACE_H_END_CLEARANCE
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

        canvas.add_connection_endpoint(
            itf, "et_itf" if self.front_panel else "ap_itf", lower_mid, upper_mid
        )
        self.itf_params[itf] = params

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
                    style="font-family:monospace",
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
                        style="font-family:monospace",
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
                        style="font-family:monospace",
                        font_size=15,
                    )
                )

        self.itf_idx += 1

    def render_blank_interface(self):
        self.itf_idx += 1


class FrontPanelPorts(InterfaceCollection):
    def __init__(self, interface_count):
        super(FrontPanelPorts, self).__init__(
            "front_panel_interfaces", interface_count, 0, True, 300
        )


class FPGAPorts(InterfaceCollection):
    APP_Y_OFFSET = (
        400
    )  # Indicates how far down apps are drawn from the top border of the FPGA box

    def __init__(
        self,
        id,
        ap_interfaces,
        fpga_apps,
        app_shapes,
        onchip_connections=None,
        onchip_conn_clearance=_ONCHIP_CONNECTION_CLEARANCE,
    ):
        self.fpga_id = id
        self.app_shapes = app_shapes
        self.fpga_apps = fpga_apps
        self.ap_interfaces = ap_interfaces
        self.apps_ports = {}
        self.onchip_connections = []
        self.onchip_endpoints = set()
        self.portless_apps = set()
        self.onchip_conn_clearance = onchip_conn_clearance

        # The height of the FPGA box is determined by the number of on-chip connections belonging only to this FPGA
        height = 750
        if onchip_connections:
            for conn in onchip_connections:
                dst = conn["dst"]
                src = conn["src"]
                if (dst in ap_interfaces or dst.startswith(id)) and (
                    src in ap_interfaces or src.startswith(id)
                ):
                    self.onchip_endpoints.add(dst)
                    self.onchip_endpoints.add(src)
                    self.onchip_connections.append(conn)
                    height += self.onchip_conn_clearance

        for app, params in self.fpga_apps.items():
            if len(set(params["ports"]) - self.onchip_endpoints) == 0:
                self.portless_apps.add(app)

        super(FPGAPorts, self).__init__(id, len(ap_interfaces), len(self.portless_apps), False, height)

    def render_fpga_internals(
        self, canvas, x, y, interfaces, itf_prefix="ap"
    ):
        self.render_box(canvas, x, y)

        sorted_apps = []
        for app, params in self.fpga_apps.items():
            avg_itf = get_average_itf_idx(params["ports"], itf_prefix)
            sorted_apps.append((app, avg_itf))
        sorted_apps = [app for app, _ in sorted(sorted_apps, key=lambda info: info[1])]

        for app in sorted_apps:
            params = self.fpga_apps[app]

            app_ports = set(params["ports"])
            self.apps_ports[app] = set(app_ports)

            onchip_app_ports = app_ports.intersection(self.onchip_endpoints)
            app_ports -= onchip_app_ports

            for itf in get_sorted_itfs(onchip_app_ports, itf_prefix):
                self.render_next_interface(canvas, itf, interfaces[itf])

            for itf in get_sorted_itfs(app_ports, itf_prefix):
                self.render_next_interface(canvas, itf, interfaces[itf])

            portless_app_x = None
            if app in self.portless_apps:
                portless_app_x = self.get_current_x()
                self.render_blank_interface()

            self.draw_app(canvas, app, params["type"], 80, app_ports, portless_app_x)

    def draw_app(self, canvas, name, app_type, size_factor, ports, portless_app_x=None):
        app = canvas.drawing.add(
            canvas.drawing.g(
                id="app_" + self.id + "_" + name, fill="white", font_size=50
            )
        )

        points = self.app_shapes[app_type]
        width = max([x for x, _ in points]) * size_factor
        height = max([y for _, y in points]) * size_factor

        itf_x_coords = [portless_app_x]
        if not portless_app_x:
            # Determine the placement of the app by selecting the mid-point of all the connected ports
            itf_coords = [canvas.ap_coords[itf] for itf in ports if itf in canvas.ap_coords]
            itf_x_coords = [x for x, _ in itf_coords]

        x_offset = min(itf_x_coords) + (max(itf_x_coords) - min(itf_x_coords)) / 2.0
        x_offset -= width / 2.0

        abs_points = [
            (
                x * size_factor + x_offset,
                y * size_factor + self.y + FPGAPorts.APP_Y_OFFSET,
            )
            for x, y in points
        ]

        path = ["M{},{}".format(*abs_points[0])] + [
            "L{},{}".format(*point) for point in abs_points[1:]
        ]
        app.add(canvas.drawing.path(path, fill="none", stroke_width=6, stroke="black"))

        x_middle = x_offset + width / 2.0
        y_middle = self.y + FPGAPorts.APP_Y_OFFSET + height / 2.0
        app.add(
            canvas.drawing.text(
                name,
                insert=(x_middle, y_middle),
                alignment_baseline="middle",
                text_anchor="middle",
                fill="black",
                stroke_width=1,
            )
        )

        app_upper_coords = (x_middle, (self.y + FPGAPorts.APP_Y_OFFSET))
        app_lower_coords = (x_middle, (self.y + FPGAPorts.APP_Y_OFFSET) + height)

        endpoint_name = "{}.{}".format(self.fpga_id, name) if self.fpga_id else name
        canvas.add_connection_endpoint(
            endpoint_name, "app", app_lower_coords, app_upper_coords
        )

    def draw_apps_connections(self, canvas):
        for name, ports in self.apps_ports.items():
            app_name = "{}.{}".format(self.fpga_id, name) if self.fpga_id else name
            for port in ports:
                receives = False
                drives = False
                dst = port
                src = app_name

                if (
                    "receives" in self.itf_params[port]
                    and self.itf_params[port]["receives"]
                ):
                    receives = True

                if (
                    "drives" in self.itf_params[port]
                    and self.itf_params[port]["drives"]
                ):
                    drives = True
                    if receives:
                        bidir = True
                    else:
                        dst = app_name
                        src = port

                bidir = receives and drives
                nodir = not receives and not drives
                canvas.render_connection(
                    dst, src, bidir=bidir, onchip=True, nodir=nodir
                )

        connection_lower_y = self.y + 700
        for conn in self.onchip_connections:
            canvas.render_square_connection(
                conn["dst"], conn["src"], conn["desc"], connection_lower_y
            )
            connection_lower_y += self.onchip_conn_clearance


def generate_system_svg(filename, *args, **kwargs):
    with open(filename, "w") as fileobj:
        generate_system_svg_stream(fileobj, *args, **kwargs)


def generate_system_svg_stream(
    stream,
    interfaces,
    connections,
    fpga_apps,
    app_shapes,
    dominant_type=None,
    onchip_connections=None,
):
    fpp = FrontPanelPorts(len(get_sorted_itfs(interfaces, "et")))

    fpga_ids = []
    fpgas = {}
    for fpga_id, apps in fpga_apps.items():
        ap_interfaces = sum([app["ports"] for app in apps.values()], [])
        fpgas[fpga_id] = FPGAPorts(
            fpga_id, ap_interfaces, apps, app_shapes, onchip_connections
        )

        # Remove the onchip connections within this FPGA
        for conn in fpgas[fpga_id].onchip_connections:
            onchip_connections.remove(conn)

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
        drawing_height = fpgas_y + fpgas_height

        if onchip_connections:
            inter_chip_connection_lower_y = (
                drawing_height + _ONCHIP_CONNECTION_CLEARANCE
            )
            drawing_height = (
                inter_chip_connection_lower_y
                + len(onchip_connections) * _ONCHIP_CONNECTION_CLEARANCE
            )
        else:
            drawing_height += _COLLECTION_SPACING / 2

    drawing = svgwrite.Drawing(
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

    # Render all the FPGAs, their interfaces and their apps
    for fpga_id in fpga_ids:
        fpgas[fpga_id].render_fpga_internals(
            canvas, fpgas_x, fpgas_y, interfaces
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
            onchip=False,
            types=get_connection_types(
                interfaces, endp1, endp2, bidir=True, dominant_type=dominant_type
            ),
        )

    for dst, src in singledir_connections.items():
        canvas.render_connection(
            dst,
            src,
            bidir=False,
            onchip=False,
            types=get_connection_types(
                interfaces, dst, src, bidir=False, dominant_type=dominant_type
            ),
        )

    for fpga_id in fpga_ids:
        fpgas[fpga_id].draw_apps_connections(canvas)

    if onchip_connections:
        for conn in onchip_connections:
            canvas.render_square_connection(
                conn["dst"], conn["src"], conn["desc"], inter_chip_connection_lower_y
            )
            inter_chip_connection_lower_y += _ONCHIP_CONNECTION_CLEARANCE

    canvas.render_legend(boxes_width, _COLLECTION_SPACING, _LEGEND_WIDTH)
    canvas.drawing.write(stream)
