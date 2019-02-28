from switch_config_render.generate_svg import generate_system_svg


# Vertices of the shapes used to represent FPGA applications
def get_hexagon_points():
    return [(0, 1.5), (1, 3), (3, 3), (4, 1.5), (3, 0), (1, 0), (0, 1.5)]


def get_mux_points():
    return [(1, 0), (0, 2), (4, 2), (3, 0), (1, 0)]


def render_high_level_example():
    # `interfaces` is a dict specifying all the front panel (et) and
    # FPGA application (ap) interfaces and their parameters
    #
    # The parameter dict can be empty or can be made up of the
    # following optional fields:
    # * alias: in case an alias is defined for this interface
    # * description: a string describing the interface
    # * receives: string or array of strings defining the network data
    #       type(s) being received by the cross connect for this interface
    # * drives: string or array of strings defining the network data
    #       type(s) being driven by the cross connect for this interface
    interfaces = {
        # Front panel ports
        "et1": {
            # et1, a.k.a. front_panel_1 receives and drives network data
            # of both type_a and type_b
            "alias": "front_panel_1",
            "description": "Front Panel 1",
            "receives": ["type_a", "type_b"],
            "drives": ["type_a", "type_b"],
        },
        "et2": {
            "alias": "front_panel_2",
            "description": "Front Panel 2",
            "receives": "type_b",
            "drives": "type_c",
        },
        "et3": {
            "alias": "front_panel_3",
            "description": "Front Panel 3",
            "receives": "type_b",
            "drives": "type_c",
        },
        "et5": {
            "alias": "front_panel_5",
            "description": "Front Panel 5",
            "receives": "type_c",
            "drives": "type_b",
        },
        "et6": {
            "alias": "front_panel_6",
            "description": "Front Panel 6",
            "receives": "type_c",
            "drives": "type_b",
        },
        "et7": {
            "alias": "front_panel_7",
            "description": "Front Panel 7",
            "receives": "type_c",
            "drives": "type_b",
        },
        "et9": {"alias": "front_panel_9", "description": "Tap Out", "drives": "tap"},
        # Every application port listed here must be associated with a application port in 'fpga_apps' below
        "ap1": {
            "alias": "custom_in",
            "description": "Custom In",
            "receives": ["type_a", "type_b"],
            "drives": ["type_a", "type_b"],
        },
        "ap2": {
            "alias": "custom_out_0",
            "description": "Custom Out 0",
            "receives": "type_c",
            "drives": "type_b",
        },
        "ap3": {
            "alias": "custom_out_1",
            "description": "Custom Out 1",
            "receives": "type_c",
            "drives": "type_b",
        },
        "ap4": {
            "alias": "mux_0_in_1",
            "description": "Mux 0 input 1",
            "drives": "type_c",
        },
        "ap5": {
            "alias": "mux_0_in_2",
            "description": "Mux 0 input 2",
            "drives": "type_c",
        },
        "ap6": {
            "alias": "mux_0_in_3",
            "description": "Mux 0 input 3",
            "drives": "type_c",
        },
        "ap7": {
            "alias": "mux_0_in_4",
            "description": "Mux 0 input 4",
            "drives": "type_c",
        },
        "ap8": {
            "alias": "mux_0_out",
            "description": "Mux 0 output",
            "receives": "type_c",
        },
        "ap57": {
            "alias": "mux_1_in_1",
            "description": "Mux 1 input 1",
            "drives": "tap",
        },
        "ap58": {
            "alias": "mux_1_in_2",
            "description": "Mux 1 input 2",
            "drives": "tap",
        },
        "ap59": {
            "alias": "mux_1_in_3",
            "description": "Mux 1 input 3",
            "drives": "tap",
        },
        "ap60": {
            "alias": "mux_1_in_4",
            "description": "Mux 1 input 4",
            "drives": "tap",
        },
        "ap61": {
            "alias": "mux_1_out",
            "description": "Mux 1 output",
            "receives": "tap",
        },
    }

    # `connections` is a dict of `key: value` pairs, where the `key`
    # defines the destination and the `value` the source of a connection
    connections = {
        "ap1": "et1",
        "et1": "ap1",
        "ap2": "et2",
        "et2": "ap2",
        "ap4": "ap3",
        "ap5": "et5",
        "ap6": "et6",
        "ap7": "et7",
        "et3": "ap8",
        "ap3": "et3",
        "et5": "et3",
        "et6": "et3",
        "et7": "et3",
        "ap57": "et1",
        "ap58": "et2",
        "ap59": "et3",
        "ap60": "ap8",
        "et9": "ap61",
    }

    # `fpga_apps` is a dict that specifies the applications that
    # are configured on the given FPGA and is composed of nested
    # dictionaries.
    #
    # The keys at the first level specify the FPGA aliases, e.g.,
    # `central_fpga`
    #
    # The keys at the second level specify the aliases of the apps
    # configured on the FPGA, e.g., `custom_0` or `mux_0`. The value
    # pointed to is a dict that must contain the following information:
    # * type: gives the app type and is used to lookup which shape
    #       needs to be drawn based on `app_shapes`
    # * ports: a list of ports associated with this app
    fpga_apps = {
        "central_fpga": {
            "custom_0": {"type": "custom", "ports": ["ap1", "ap2", "ap3"]},
            "mux_0": {"type": "mux", "ports": ["ap4", "ap5", "ap6", "ap7", "ap8"]},
        },
        "leaf_a_fpga": {
            "mux_1": {"type": "mux", "ports": ["ap57", "ap58", "ap59", "ap60", "ap61"]}
        },
    }

    # `app_shapes` defines the vertices of the shapes to be used for
    # the applications defined in `fpga_apps`
    app_shapes = {"custom": get_hexagon_points(), "mux": get_mux_points()}

    # `onchip_connections` specifies internal connectivity within the FPGA and between FPGAs,
    # between `ap` interfaces and FPGA applications
    onchip_connections = [
        {"dst": "central_fpga.mux_0", "src": "ap1", "desc": "Mux control"},
        {"dst": "central_fpga.custom_0", "src": "ap8", "desc": "Status interface"},
        {
            "dst": "leaf_a_fpga.mux_1",
            "src": "central_fpga.custom_0",
            "desc": "Muxed output for custom_0",
        },
    ]

    # Generate the SVG. `dominant_type` can be used to define an interface type that will override all other types
    generate_system_svg(
        "high_level_example.svg",
        interfaces,
        connections,
        fpga_apps,
        app_shapes,
        dominant_type="tap",
        onchip_connections=onchip_connections,
    )
