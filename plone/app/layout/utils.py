from zope.i18n import translate
from zope.publisher.interfaces.browser import IBrowserRequest

from Acquisition import aq_base
from Acquisition import aq_get
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName

try:
    from Products.LinguaPlone.interfaces import ITranslatable
    HAS_LP = True
except ImportError:
    HAS_LP = False

_marker = []


def getEmptyTitle(context, translated=True):
    """Returns string to be used for objects with no title or id"""
    # The default is an extra fancy unicode elipsis
    empty = unicode('\x5b\xc2\xb7\xc2\xb7\xc2\xb7\x5d', 'utf-8')
    if translated:
        if context is not None:
            if not IBrowserRequest.providedBy(context):
                context = aq_get(context, 'REQUEST', None)
        empty = translate('title_unset', domain='plone', context=context, default=empty)
    return empty


def isIDAutoGenerated(context, id):
    # In 2.1 non-autogenerated is the common case, caught exceptions are
    # expensive, so let's make a cheap check first
    if id.count('.') < 2:
        return False

    pt = getToolByName(context, 'portal_types')
    portaltypes = pt.listContentTypes()
    portaltypes.extend([pt.lower() for pt in portaltypes])

    try:
        parts = id.split('.')
        random_number = parts.pop()
        date_created = parts.pop()
        obj_type = '.'.join(parts)
        type = ' '.join(obj_type.split('_'))
        # New autogenerated ids may have a lower case portal type
        if ((type in portaltypes or obj_type in portaltypes) and
            DateTime(date_created) and
            float(random_number)):
            return True
    except (ValueError, AttributeError, IndexError, DateTime.DateTimeError):
        pass

    return False


def lookupTranslationId(obj, page, ids):
    if not HAS_LP:
        return page
    implemented = ITranslatable.providedBy(obj)
    if not implemented or implemented and not obj.isTranslation():
        pageobj = getattr(obj, page, None)
        if (pageobj is not None and
            ITranslatable.providedBy(pageobj)):
            translation = pageobj.getTranslation()
            if (translation is not None and
                translation.getId() in ids):
                page = translation.getId()
    return page


def pretty_title_or_id(context, obj, empty_value=_marker):
    """Return the best possible title or id of an item, regardless
       of whether obj is a catalog brain or an object, but returning an
       empty title marker if the id is not set (i.e. it's auto-generated).
    """
    title = None
    if getattr(aq_base(obj), 'Title', None) is not None:
        title = getattr(obj, 'Title', None)
    if callable(title):
        title = title()
    if title:
        return title
    item_id = getattr(obj, 'getId', None)
    if callable(item_id):
        item_id = item_id()
    if item_id and not isIDAutoGenerated(context, item_id):
        return item_id
    if empty_value is _marker:
        empty_value = getEmptyTitle(context)
    return empty_value


def safe_unicode(value):
    if isinstance(value, unicode):
        return value
    elif isinstance(value, basestring):
        try:
            value = unicode(value, 'utf-8')
        except UnicodeDecodeError:
            value = value.decode('utf-8', 'replace')
    return value
