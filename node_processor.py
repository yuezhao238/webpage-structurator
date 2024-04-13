def leaf_list(element):
    leaf_node_list = []

    def get_leaf_node(element):
        if 'children' not in element:
            if all([element['boxInfo'][key] > 0 for key in ['height', 'width', 'top', 'left']]):
                leaf_node_list.append(element)
        else:
            for child in element['children']:
                get_leaf_node(child)

    get_leaf_node(element)
    return leaf_node_list
