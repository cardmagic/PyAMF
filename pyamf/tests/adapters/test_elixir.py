# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
PyAMF SQLAlchemy adapter tests.

@since 0.4
"""

import unittest

from elixir import * # <-- import * sucks

import pyamf
from pyamf.adapters import _sqlalchemy_orm as adapter


class Genre(Entity):
    name = Field(Unicode(15), primary_key=True)
    movies = ManyToMany('Movie')

    def __repr__(self):
        return '<Genre "%s">' % self.name


class Movie(Entity):
    title = Field(Unicode(30), primary_key=True)
    year = Field(Integer, primary_key=True)
    description = Field(UnicodeText, deferred=True)
    director = ManyToOne('Director')
    genres = ManyToMany('Genre')

    def __repr__(self):
        return '<Movie "%s" (%d)>' % (self.title, self.year)


class Director(Entity):
    name = Field(Unicode(60))
    movies = OneToMany('Movie')

    def __repr__(self):
        return '<Director "%s">' % self.name


# set up
metadata.bind = "sqlite://"
setup_all()


class BaseTestCase(unittest.TestCase):
    """
    Initialise up all table/mappers.
    """

    def setUp(self):
        create_all()

        self.movie_alias = pyamf.register_class(Movie, 'movie')
        self.genre_alias = pyamf.register_class(Genre, 'genre')
        self.director_alias = pyamf.register_class(Director, 'director')

        self.create_movie_data()

    def tearDown(self):
        drop_all()
        session.rollback()
        session.expunge_all()

        pyamf.unregister_class(Movie)
        pyamf.unregister_class(Genre)
        pyamf.unregister_class(Director)

    def create_movie_data(self):
        scifi = Genre(name=u"Science-Fiction")
        rscott = Director(name=u"Ridley Scott")
        glucas = Director(name=u"George Lucas")
        alien = Movie(title=u"Alien", year=1979, director=rscott, genres=[scifi, Genre(name=u"Horror")])
        brunner = Movie(title=u"Blade Runner", year=1982, director=rscott, genres=[scifi])
        swars = Movie(title=u"Star Wars", year=1977, director=glucas, genres=[scifi])

        session.commit()
        session.expunge_all()


class ClassAliasTestCase(BaseTestCase):
    def test_type(self):
        self.assertIdentical(
            self.movie_alias.__class__, adapter.SaMappedClassAlias)
        self.assertIdentical(
            self.genre_alias.__class__, adapter.SaMappedClassAlias)
        self.assertIdentical(
            self.director_alias.__class__, adapter.SaMappedClassAlias)

    def test_get_attrs(self):
        m = Movie.query.filter_by(title=u"Blade Runner").one()

        static, dynamic = self.movie_alias.getEncodableAttributes(m)

        print static, dynamic


class ApplyAttributesTestCase(unittest.TestCase):
    def test_undefined(self):
        u = self.alias.createInstance()

        attrs = {
            'sa_lazy': ['another_lazy_loaded'],
            'sa_key': [None],
            'addresses': [],
            'lazy_loaded': [],
            'another_lazy_loaded': pyamf.Undefined, # <-- the important bit
            'id': None,
            'name': 'test_user'
        }

        self.alias.applyAttributes(u, attrs)

        d = u.__dict__.copy()

        if sqlalchemy.__version__.startswith('0.4'):
            self.assertTrue('_state' in d)
            del d['_state']
        elif sqlalchemy.__version__.startswith('0.5'):
            self.assertTrue('_sa_instance_state' in d)
            del d['_sa_instance_state']

        self.assertEquals(d, {
            'lazy_loaded': [],
            'addresses': [],
            'name': 'test_user',
            'id': None
        })

    def test_decode_unaliased(self):
        u = self.alias.createInstance()

        attrs = {
            'sa_lazy': [],
            'sa_key': [None],
            'addresses': [],
            'lazy_loaded': [],
            # this is important because we haven't registered AnotherLazyLoaded
            # as an alias and the decoded object for an untyped object is an
            # instance of pyamf.ASObject
            'another_lazy_loaded': [pyamf.ASObject({'id': 1, 'user_id': None})],
            'id': None,
            'name': 'test_user'
        }

        # sqlalchemy can't find any state to work with
        self.assertRaises(AttributeError, self.alias.applyAttributes, u, attrs)


class AdapterTestCase(BaseTestCase):
    """
    Checks to see if the adapter will actually intercept a class correctly.
    """

    def test_mapped(self):
        self.assertNotEquals(None, adapter.class_mapper(User))
        self.assertTrue(adapter.is_class_sa_mapped(User))

    def test_instance(self):
        u = User()

        self.assertTrue(adapter.is_class_sa_mapped(u))

    def test_not_mapped(self):
        self.assertRaises(adapter.UnmappedInstanceError, adapter.class_mapper, Spam)
        self.assertFalse(adapter.is_class_sa_mapped(Spam))


def suite():
    suite = unittest.TestSuite()

    try:
        import pysqlite2
    except ImportError:
        return suite

    classes = [
        ClassAliasTestCase,
        #AdapterTestCase,
        #ClassAliasTestCase,
        #ApplyAttributesTestCase
    ]

    for x in classes:
        suite.addTest(unittest.makeSuite(x))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
