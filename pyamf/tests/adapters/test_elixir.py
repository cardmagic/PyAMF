# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
PyAMF SQLAlchemy adapter tests.

@since 0.4
"""

import unittest

import elixir as e

import pyamf
from pyamf.adapters import _elixir as adapter
from pyamf.tests.util import Spam


class Genre(e.Entity):
    name = e.Field(e.Unicode(15), primary_key=True)
    movies = e.ManyToMany('Movie')

    def __repr__(self):
        return '<Genre "%s">' % self.name


class Movie(e.Entity):
    title = e.Field(e.Unicode(30), primary_key=True)
    year = e.Field(e.Integer, primary_key=True)
    description = e.Field(e.UnicodeText, deferred=True)
    director = e.ManyToOne('Director')
    genres = e.ManyToMany('Genre')


class Person(e.Entity):
    name = e.Field(e.Unicode(60), primary_key=True)


class Director(Person):
    movies = e.OneToMany('Movie')
    e.using_options(inheritance='multi')


# set up
e.metadata.bind = "sqlite://"
e.setup_all()


class BaseTestCase(unittest.TestCase):
    """
    Initialise up all table/mappers.
    """

    def setUp(self):
        e.create_all()

        self.movie_alias = pyamf.register_class(Movie, 'movie')
        self.genre_alias = pyamf.register_class(Genre, 'genre')
        self.director_alias = pyamf.register_class(Director, 'director')

        self.create_movie_data()

    def tearDown(self):
        e.drop_all()
        e.session.rollback()
        e.session.expunge_all()

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

        e.session.commit()
        e.session.expunge_all()


class ClassAliasTestCase(BaseTestCase):
    def test_type(self):
        self.assertEqual(
            self.movie_alias.__class__, adapter.ElixirAdapter)
        self.assertEqual(
            self.genre_alias.__class__, adapter.ElixirAdapter)
        self.assertEqual(
            self.director_alias.__class__, adapter.ElixirAdapter)

    def test_get_attrs(self):
        m = Movie.query.filter_by(title=u"Blade Runner").one()

        g = m.genres[0]
        d = m.director

        static, dynamic = self.movie_alias.getEncodableAttributes(m)

        self.assertEquals(static, {
            'genres': [g],
            'description': None,
            'title': u'Blade Runner',
            'director': d,
            'year': 1982
        })

        self.assertEquals(dynamic, {'sa_key': [u'Blade Runner', 1982], 'sa_lazy': []})

    def test_inheritance(self):
        d = Director.query.filter_by(name=u"Ridley Scott").one()

        print self.director_alias.getEncodableAttributes(d)


def suite():
    suite = unittest.TestSuite()

    try:
        import pysqlite2
    except ImportError:
        return suite

    classes = [
        ClassAliasTestCase,
    ]

    for x in classes:
        suite.addTest(unittest.makeSuite(x))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
