from ...utils import FrozenDict


class OpenC2MessageFormats(FrozenDict):
    def __init__(self, *args, **kwargs):
        self._hash = None
        super(FrozenDict, self).__init__(
            JSON='json',
            CBOR='cbor',
            ProtoBuf='proto',
            XML='xml'
        )

    @staticmethod
    def list(val=False):
        """
        Structure the message format types as a list
        :return: List of types
        :rtype: list
        """
        tmp = []
        for f in dir(OpenC2MessageFormats):
            if not f.startswith(('_', 'dict', 'list')):
                if val:
                   tmp.append(getattr(OpenC2MessageFormats, f))
                else:
                    tmp.append(f)

        return tmp

    @staticmethod
    def dict(valKey=False):
        """
        Structure the message format types names and values as a dictionary
        :param valKey: bool for use of the name or value as hte key
        :return:
        """
        tmp = {}
        for f in dir(OpenC2MessageFormats):
            if not f.startswith(('_', 'dict', 'list')):
                if valKey:
                    tmp[getattr(OpenC2MessageFormats, f)] = f
                else:
                    tmp[f] = getattr(OpenC2MessageFormats, f)

        return tmp
