
def get_idx(prefix, itf):
    """
    Gets the index of an interface string
    >>> get_idx('et', 'et12')
    12

    >>> get_idx('ap', 'ap32')
    32
    """
    return int(itf[len(prefix) :])


def get_sorted_itfs(itfs, prefix):
    """
    Gets a sorted list of interfaces for the given interface prefix
    >>> get_sorted_itfs(['ap21', 'et3', 'ap12', 'et5', 'et1'], 'et')
    ['et1', 'et3', 'et5']

    >>> get_sorted_itfs(['ap21', 'et3', 'ap12', 'et5', 'et1'], 'ap')
    ['ap12', 'ap21']
    """
    itfs = [itf for itf in itfs if itf.startswith(prefix)]
    return sorted(itfs, key=lambda x: get_idx(prefix, x))


def get_average_itf_idx(itfs, prefix):
    """
    Gets the average index of interfaces with matching prefix from a
    list of prefixes
    >>> get_average_itf_idx(['et3', 'et5', 'et1'], 'et')
    3.0
    """
    return sum([get_idx(prefix, itf) for itf in itfs]) / float(len(itfs))


def get_connection_types(itfs, dst, src, bidir, dominant_type=None):
    """
    Gets the types of a connection depending on the source and
    destination types. Determines the overlapping "drives" and "receives"
    types for the destination and source respectively. If the connection
    is bidirectional then the "drives" and "receives" types of both
    destination and source are taken into account.

    >>> itfs = {}
    >>> itfs['et1'] = { 'receives': ['type_a'], 'drives': 'type_b' }
    >>> itfs['ap1'] = { 'receives': ['type_b', 'type_c'], 'drives': 'type_a' }
    >>> itfs['ap2'] = { 'drives': ['type_b', 'type_c'] }

    >>> get_connection_types(itfs, 'ap1', 'et1', bidir=False)
    ('type_a',)

    >>> get_connection_types(itfs, 'et1', 'ap1', bidir=False)
    ('type_b',)

    >>> get_connection_types(itfs, 'et1', 'ap1', bidir=True)
    ('type_a', 'type_b')

    >>> get_connection_types(itfs, 'ap2', 'ap1', bidir=False)
    ('type_b', 'type_c')

    >>> get_connection_types(itfs, 'ap2', 'ap1', bidir=False, dominant_type='type_c')
    ('type_c',)
    """

    def get(itf, direction_types):
        if not direction_types in itf:
            return set()
        if isinstance(itf[direction_types], str):
            return set([itf[direction_types]])
        return set(itf[direction_types])

    driving_types = get(itfs[dst], "drives")
    receiving_types = get(itfs[src], "receives")

    if bidir:
        # If the connection is bidirectional we also take all the types
        # in the opposite direction into account
        driving_types.update(get(itfs[dst], "receives"))
        receiving_types.update(get(itfs[src], "drives"))

    if dominant_type in driving_types or dominant_type in receiving_types:
        # A dominant type will override any other types for the given connection
        return (dominant_type,)

    return tuple(sorted(driving_types & receiving_types))
