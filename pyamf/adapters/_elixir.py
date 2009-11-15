# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Elixir adapter module. Elixir adds a number of properties to the mapped instances

@see: U{SQLAlchemy homepage (external)<http://elixir.ematia.de>}

@since: 0.6
"""

from pyamf.adapters import _sqlalchemy_orm as adapter


adapter.SaMappedClassAlias.EXCLUDED_ATTRS.append('_global_session')
