import inspect
from itertools import groupby
from sys import _getframe
try:
    basestring
except NameError:
    basestring = (str, bytes) #python3

from colorama import init

from .constants import ATTR_MAP, CLASS, DEFAULT_CATEGORY, FUNCTION
from .format import format_category

init()  # To support Windows.


class PrettyDir(object):
    """Class that provides pretty dir and search API."""

    def __init__(self, obj=None, filter_func=None):
        self.obj = obj
        self.attrs = []
        if obj is None:
            source = _getframe(1).f_locals
        else:
            if isinstance(self.obj, basestring):
                self.obj = self.import_from_str(obj)
            source = {name: self.__getattr(name) for name in dir(self.obj)}
        self.__inspect_category(source)

    def __repr__(self):
        output = []
        for category, attrs in groupby(self.attrs, lambda x: x.category):
            output.append(format_category(category, attrs))

        output.sort(key=lambda x: x[0])
        return '\n'.join(category_output[1] for category_output in output)

    def __len__(self):
        return len(self.attrs)

    def __getitem__(self, index):
        return self.attrs[index].name

    def search(self, term, case_sensitive=False):
        """Search for names that match some pattern.

        Args:
            term: String used to match names. A name is returned if it matches
              the whole search term.
            case_sensitive: Boolean to match case or not, default is False
              (case insensitive)

        Return:
            A PrettyDir object with matched names.
        """
        if case_sensitive:
            self.attrs = [attr for attr in self.attrs if term in attr.name]
        else:
            term = term.lower()
            self.attrs = [
                attr for attr in self.attrs if term in attr.name.lower()
            ]
        return self

    s = search

    def __getattr(self, attr):
        """A wrapper around getattr(), handling some exceptions."""
        obj_name = getattr(self.obj, '__name__', '')
        if obj_name == 'DataFrame' and attr in ('columns', 'index'):
            return []  # So columns falls into DEFAULT_CATEGORY.
        return getattr(self.obj, attr)

    def __inspect_category(self, source):
        for name, attribute in source.items():
            category = ATTR_MAP.get(name, self.get_category(attribute))
            if isinstance(category, list):
                for selector, real_category in category:
                    if selector(self.obj):
                        category = real_category
                        break
                else:
                    raise ValueError('category not match: ' + name)
            doc = self.get_oneline_doc(attribute)
            self.attrs.append(PrettyAttribute(name, category, doc))

        self.attrs.sort(key=lambda x: (x.category, x.name))

    @staticmethod
    def import_from_str(obj_name):
        obj_list = obj_name.split('.')
        obj = __import__(obj_list.pop(0))
        for attr in obj_list:
            obj = getattr(obj, attr)
        return obj

    @staticmethod
    def get_oneline_doc(attribute):
        if hasattr(attribute, '__doc__'):
            doc = inspect.getdoc(attribute)
            return doc.split('\n', 1)[0] if doc else ''  # default doc is None
        return None

    @staticmethod
    def get_category(attribute):
        if inspect.isclass(attribute):
            return CLASS
        elif inspect.isfunction(attribute):
            return FUNCTION
        elif inspect.ismethod(attribute):
            return FUNCTION
        elif inspect.isbuiltin(attribute):
            return FUNCTION
        elif inspect.ismethoddescriptor(attribute):  # list.append
            return FUNCTION
        else:
            return DEFAULT_CATEGORY


class PrettyAttribute(object):
    def __init__(self, name, category, doc=None):
        self.name = name
        self.category = category
        self.doc = doc

    def __repr__(self):
        return '%s: %s' % (self.name, self.category)
