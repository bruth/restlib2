from xml.etree import cElementTree as ET

class DataOrientedXML(object):
    """A data oriented XML encoder/decoder.

    A few rules that are enforced:

        - element attributes are ignored if subelements exist
        - elements that contain subelements of the same tag name are assumed
        to be strictly containers, i.e. element text will be ignored

    """
    def _decode(self, parent, converters, path=None):
        if path is None:
            path = []
        # assume each subelement to be a property of the parent, rather
        # than a list of items of the same type (e.g. tag name). if at
        # any point there are duplicates the property will turn in a list
        # of values
        node = {}

        if len(parent) > 0:
            # iterate over each subelement and add it to the node
            for child in iter(parent):
                tag = child.tag
                subnode = self._decode(child, converters, path + [tag])

                # if this is true, there are multiple elements with this tag name.
                # the value of this entry must now turn into a list
                if node.has_key(tag):
                    # if this is true, we must take the existing value and insert it
                    # at the beginning of the list
                    if type(node[tag]) is not list:
                        node[tag] = [node[tag]]
                    # recurse
                    node[tag].append(subnode)

                # first element with this tag, we assume there will be a single
                # instance
                else:
                    node[tag] = subnode

        # if no subelements exist, just treat it as a set of attributes or the
        # text value if no element attributes are defined
        else:
            # if no text exists (or if its all whitespace), then we set text to None
            # here
            if not parent.text or not parent.text.strip():
                text = None
            else:
                # check if a converter exist for this tag
                _path = '/'.join(path)
                if converters.has_key(_path):
                    text = converters[_path](parent.text)
                else:
                    text = parent.text

            if parent.attrib:
                node.update(parent.attrib)
                # if the text is not only whitespace, add it to the node
                node['text'] = text
            else:
                node = text

        return node

    def _encode(self, data, parent):

        # each key becomes a new node, recurse the the value
        if isinstance(data, dict):
            for k, v in data.iteritems():
                node = ET.Element(k)
                self._encode(v, node)
                parent.append(node)

        # iterate over each item in the list keeping the
        # parent the same
        elif isinstance(data, (list, tuple)):
            for i in iter(data):
                self._encode(i, parent)

        # treat as some primitive value and convert it to a string
        else:
            parent.text = str(data)

        return parent

    def decode(self, text, converters=None, **kwargs):
        if not converters:
            converters = {}
        root = ET.XML(text)
        return self._decode(root, converters)

    def encode(self, data, root_tag='root', **kwargs):
        root = ET.Element(root_tag)
        return ET.tostring(self._encode(data, root), 'utf-8')

