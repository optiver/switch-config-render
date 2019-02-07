import colorsys


class Canvas(object):
    # An exquisite, hand-picked selection of colours that are easy to
    # distinguish. Scanning linearly yields a lot of green
    # Note: not colour-vision deficiency optimised
    HUES = [0.0, 0.091, 0.15, 0.305, 0.475, 0.563, 0.68, 0.764, 0.883]

    def __init__(self, drawing):
        self.drawing = drawing

        self.x_connect_src_endpoints = {}
        self.x_connect_dst_endpoints = {}
        self.ap_src_coords = {}
        self.ap_dst_coords = {}
        self.on_chip_src_coords = {}
        self.on_chip_dst_coords = {}

        self.ap_coords = {}
        self.connections = None

        # Create the arrowhead markers
        self.end_marker = drawing.marker(insert=(5, 3), size=(6, 6), orient="auto")
        self.end_marker.add(
            drawing.path(["M1,1", "L1,5", "L5,3", "L1,1"], fill="black")
        )
        self.start_marker = drawing.marker(insert=(1, 3), size=(6, 6), orient="auto")
        self.start_marker.add(
            drawing.path(["M1,3", "L5,5", "L5,1", "L1,3"], fill="black")
        )
        drawing.defs.add(self.end_marker)
        drawing.defs.add(self.start_marker)

        self.connection_colours = {}
        self.hue_idx = 0
        self.saturation = 0.9

    def get_colour_for_types(self, types):
        if types in self.connection_colours:
            return self.connection_colours[types]

        rgb = colorsys.hls_to_rgb(Canvas.HUES[self.hue_idx], 0.5, self.saturation)
        rgb_255 = tuple(int(255 * v) for v in rgb)

        self.hue_idx += 1
        if self.hue_idx >= len(Canvas.HUES):
            self.hue_idx = 0
            self.saturation -= 0.2
            if self.saturation <= 0.0:
                self.saturation = 1.0

        self.connection_colours[types] = "#{:02X}{:02X}{:02X}".format(*rgb_255)
        return self.connection_colours[types]

    def render_connection(self, dst, src, bidir, onchip, types=None, nodir=False):
        # The connections need to be rendered at the top level of the SVG, so the connections group needs to be added last
        if self.connections is None:
            self.connections = self.drawing.add(
                self.drawing.g(id="connection", stroke="black")
            )

        dst_endpoints = self.ap_dst_coords if onchip else self.x_connect_dst_endpoints
        src_endpoints = self.ap_src_coords if onchip else self.x_connect_src_endpoints

        dst_coords = dst_endpoints[dst]
        src_coords = src_endpoints[src]

        # Src coords are slightly to the left, while dst coords are slightly to the right of the connection point.
        # If the connection is bidirectional we want the src coords to be slightly to the right so that the direction
        # of other connections that are sourced from this endpoint are easy to tell apart
        if bidir:
            src_coords = dst_endpoints[src]

        line = self.connections.add(
            self.drawing.path(
                ["M" + src_coords[0], "C" + src_coords[1]] + dst_coords[::-1],
                fill="none",
                stroke=self.get_colour_for_types(types) if types else "black",
                stroke_width=4 if onchip else 6,
            )
        )
        if not nodir:
            if bidir:
                line.set_markers((self.start_marker, None, self.end_marker))
            else:
                line.set_markers((None, None, self.end_marker))

    def add_connection_endpoint(
        self, endpoint_name, endpoint_type, lower_mid, upper_mid
    ):
        def bezier_coords(coords, x_offset=0, y_offset=0):
            return "{},{}".format(str(coords[0] + x_offset), str(coords[1] + y_offset))

        if endpoint_type == "et_itf":
            self.x_connect_src_endpoints[endpoint_name] = [
                bezier_coords(lower_mid, x_offset=-30),
                bezier_coords(lower_mid, x_offset=-30, y_offset=300),
            ]
            self.x_connect_dst_endpoints[endpoint_name] = [
                bezier_coords(lower_mid, x_offset=30),
                bezier_coords(lower_mid, x_offset=30, y_offset=300),
            ]
        elif endpoint_type == "ap_itf":
            self.x_connect_src_endpoints[endpoint_name] = [
                bezier_coords(upper_mid, x_offset=-30),
                bezier_coords(upper_mid, x_offset=-30, y_offset=-300),
            ]
            self.x_connect_dst_endpoints[endpoint_name] = [
                bezier_coords(upper_mid, x_offset=30),
                bezier_coords(upper_mid, x_offset=30, y_offset=-300),
            ]
            self.ap_src_coords[endpoint_name] = [
                bezier_coords(lower_mid, x_offset=30),
                bezier_coords(lower_mid, x_offset=30, y_offset=120),
            ]
            self.ap_dst_coords[endpoint_name] = [
                bezier_coords(lower_mid, x_offset=-30),
                bezier_coords(lower_mid, x_offset=-30, y_offset=120),
            ]
            self.ap_coords[endpoint_name] = lower_mid
        elif endpoint_type == "app":
            self.ap_src_coords[endpoint_name] = [
                bezier_coords(upper_mid, x_offset=-30),
                bezier_coords(upper_mid, x_offset=-30, y_offset=-120),
            ]
            self.ap_dst_coords[endpoint_name] = [
                bezier_coords(upper_mid, x_offset=30),
                bezier_coords(upper_mid, x_offset=30, y_offset=-120),
            ]
            self.on_chip_src_coords[endpoint_name] = [
                bezier_coords(lower_mid, x_offset=-30),
                bezier_coords(lower_mid, x_offset=-30, y_offset=300),
            ]
            self.on_chip_dst_coords[endpoint_name] = [
                bezier_coords(lower_mid, x_offset=30),
                bezier_coords(lower_mid, x_offset=30, y_offset=300),
            ]
        else:
            assert False, 'Unkown endpoint type "{}"'.format(endpoint_type)

    def render_legend(self, x_offset, y_offset, legend_width):
        inter_line_gap = 40
        inter_item_spacing = 20
        legend = self.drawing.add(
            self.drawing.g(id="legend", fill="black", stroke_width=6)
        )
        y = y_offset
        for connection_types, connection_colour in self.connection_colours.items():
            start_line = (x_offset, y)
            end_line = (x_offset + legend_width / 2, y)
            legend.add(
                self.drawing.line(start_line, end_line, stroke=connection_colour)
            )
            y += inter_line_gap

            for idx, connection_type in enumerate(connection_types):
                text = connection_type
                if idx < len(connection_types) - 1:
                    text += " &"
                start_text = (x_offset, y)
                legend.add(
                    self.drawing.text(str(text), insert=start_text, font_size=30)
                )
                y += inter_line_gap

            y += inter_item_spacing
