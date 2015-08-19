#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski, S. Łęski (Laboratory of            #
#    Neuroinformatics; Nencki Institute of Experimental Biology)              #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################

import unittest
from datetime import datetime, timedelta

import pytz

from ICNodes import Animal, Visit, Nosepoke
from _TestTools import allInstances, Mock, MockIntDictManager, \
                       MockCageManager, MockStrDictManager, MockCloneable, \
                       BaseTest


class ICNodeTest(BaseTest):
  def checkReadOnly(self, obj):
    for attr in self.attributes:
      try:
        self.assertRaises(AttributeError, lambda: setattr(obj, attr, attr))

      except AssertionError:
        print attr
        raise

  def checkDel(self, obj):
    attrPrefix = '_' + obj.__class__.__name__
    obj._del_()

    for attr in obj.__slots__:
      try:
        self.assertRaises(AttributeError,
                          lambda: getattr(obj, attrPrefix + attr))
      except AssertionError:
        print attr
        raise

  def checkSlots(self, obj):
    self.assertRaises(AttributeError,
                      lambda: setattr(obj, 'nonexistentAttribute', None))
    self.assertFalse('__dict__' in dir(obj))


class TestAnimal(ICNodeTest):
  attributes = ['Name', 'Tag', 'Sex', 'Notes']

  def setUp(self):
    self.mickey = Animal(u'Mickey', frozenset({'2'}), u'male', frozenset({u'bla'}))

  def testCreate(self):
    self.assertEqual(self.mickey.Name, 'Mickey')
    self.assertEqual(self.mickey.Tag, {'2'})
    self.assertEqual(self.mickey.Sex, 'male')
    self.assertEqual(self.mickey.Notes, {'bla'})


  def testFromRow(self):
    jerry = Animal.fromRow('Jerry', '1', None, None)
    self.checkAttributes(jerry,
                         [('Name', 'Jerry', unicode),
                          ('Tag', {'1'}, frozenset),
                          'Sex',
                          ('Notes', frozenset(), frozenset)
                         ])
    self.assertTrue(allInstances(jerry.Tag, unicode))

    mickey = Animal.fromRow('Mickey', '2', 'male', 'note')
    self.checkAttributes(mickey,
                         [('Name', 'Mickey', unicode),
                          ('Tag', {'2'}, frozenset),
                          ('Sex', 'male', unicode),
                          ('Notes', {'note'}, frozenset)
                         ])
    self.assertTrue(allInstances(mickey.Tag, unicode))
    self.assertTrue(allInstances(mickey.Notes, unicode))

  def testClone(self):
    animal = self.mickey.clone()
    for attr in self.attributes:
      if attr != 'Nosepokes':
        self.assertEqual(getattr(animal, attr),
                         getattr(self.mickey, attr))

  def testEq(self):
    self.assertTrue(self.mickey == Animal.fromRow('Mickey', '2'))
    self.assertTrue(Animal.fromRow('Mickey', '2') == self.mickey)
    self.assertFalse(self.mickey == Animal.fromRow('Jerry', '2'))
    self.assertFalse(self.mickey == Animal.fromRow('Mickey', '2', Sex='female'))

    animal = Animal.fromRow(u'b\xf3br', '1')
    self.assertTrue(animal == 'b\xc3\xb3br')
    self.assertFalse(animal == 'bobr')

    self.assertTrue(animal == u'b\xf3br')
    self.assertFalse(animal == u'b\xc3\xb3br')

  def testNeq(self):
    self.assertTrue(self.mickey != Animal.fromRow('Jerry', '2'))
    self.assertTrue(self.mickey != Animal.fromRow('Mickey', '2', Sex='female'))
    self.assertFalse(self.mickey != Animal.fromRow('Mickey', '2'))

    animal = Animal(u'b\xf3br', '1')
    self.assertFalse(animal != 'b\xc3\xb3br')
    self.assertTrue(animal != 'bobr')
    self.assertFalse(animal != u'b\xf3br')
    self.assertTrue(animal != u'b\xc3\xb3br')

  def testHash(self):
    self.assertEqual(hash(self.mickey), hash('Mickey'))

  def testStr(self):
    animal = Animal.fromRow(u'b\xf3br', '1')
    self.assertEqual(str(animal), 'b\xc3\xb3br')
    self.assertIsInstance(str(animal), str)

  def testUnicode(self):
    animal = Animal.fromRow(u'b\xf3br', '1')
    self.assertEqual(unicode(animal), u'b\xf3br')
    self.assertIsInstance(unicode(animal), unicode)


  def testMerge(self):
    mouse = Animal.fromRow('Mickey', '1')
    mouse.merge(self.mickey)
    self.assertEqual(mouse.Sex, 'male')
    self.assertEqual(mouse.Notes, {'bla'})
    self.assertEqual(mouse.Tag, {'1', '2'})
    self.assertIsInstance(mouse.Tag, frozenset)

    mouse.merge(Animal.fromRow('Mickey', '1'))
    self.assertEqual(mouse.Sex, 'male')


    self.assertRaises(Animal.DifferentMouse,
                      lambda: Animal.fromRow('Minnie', '1').merge(self.mickey))
    self.assertRaises(Animal.DifferentMouse,
                      lambda: Animal.fromRow('Mickey', '1', 'female').merge(self.mickey))

    mouse = Animal.fromRow('Mickey', '1', Notes='ble')
    mouse.merge(self.mickey)
    self.assertEqual(mouse.Notes, {'ble', 'bla'})
    mouse.merge(self.mickey)
    self.assertEqual(mouse.Notes, {'ble', 'bla'})

  def testRepr(self):
    self.assertEqual(repr(self.mickey), u'< Animal Mickey (male; Tag: 2) >')
    mouse = Animal.fromRow('Jerry', '1')
    self.assertEqual(repr(mouse), u'< Animal Jerry (Tag: 1) >')
    mouse.merge(Animal.fromRow('Jerry', ' 2'))
    self.assertEqual(repr(mouse), u'< Animal Jerry (Tags: 1, 2) >')

  def testReadOnly(self):
    self.checkReadOnly(self.mickey)

  def testSlots(self):
    self.checkSlots(self.mickey)

  def testDel(self):
    self.checkDel(self.mickey)


class TestVisit(ICNodeTest):
  attributes = ('Start', 'Corner', 'End', 'Module', 'Cage',
                'CornerCondition', 'PlaceError',
                'AntennaNumber', 'AntennaDuration',
                'PresenceNumber', 'PresenceDuration',
                'VisitSolution',
                '_source', '_line',
                'Nosepokes')

  def setUp(self):
    self.start = datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc)
    self.end = datetime(1970, 1, 1, 0, 5, 15, tzinfo=pytz.utc)
    self.nosepokes = tuple(MockCloneable(Duration = timedelta(seconds=10.25 * i),
                                         LickNumber = i - 1,
                                         LickDuration = timedelta(seconds=0.25 * i),
                                         LickContactTime= timedelta(seconds=0.125 * i))\
                           for i in xrange(1, 5))
    self.visit = Visit(self.start, 2, 'animal', self.end, 'mod', 4,
                       1, 0,
                       2, timedelta(seconds=12.125),
                       7, timedelta(seconds=8.5),
                       0,
                       'source', 1,
                       self.nosepokes,
                       )
    self.minimalVisit = Visit(self.start, 2, 'animal')

  def testCreate(self):
    #_vid
    self.checkAttributes(self.minimalVisit, [('Start', self.start),
                                             ('Corner', 2),
                                             ('Animal', 'animal'),
                                             'End', 'Module', 'Cage',
                                             'CornerCondition', 'PlaceError',
                                             'AntennaNumber', 'AntennaDuration',
                                             'PresenceNumber', 'PresenceDuration',
                                             'VisitSolution',
                                             '_source', '_line',
                                             'Nosepokes',
                                             ])

    self.checkAttributes(self.visit, [('Start', self.start),
                                      ('Corner', 2),
                                      ('Animal', 'animal'),
                                      ('End', self.end),
                                      ('Module', 'mod'),
                                      ('Cage', 4),
                                      ('CornerCondition', 1),
                                      ('PlaceError', 0),
                                      ('AntennaNumber', 2),
                                      ('AntennaDuration', timedelta(seconds=12.125)),
                                      ('PresenceNumber', 7),
                                      ('PresenceDuration', timedelta(seconds=8.5)),
                                      ('VisitSolution', 0),
                                      ('_source', 'source'),
                                      ('_line', 1),
                                      ('Nosepokes', self.nosepokes),
                                      ])

  def testClone(self):
    sideManager = MockIntDictManager()
    cageManager = MockCageManager({'getSideManager': {(4, 2): sideManager}})
    sourceManager = MockStrDictManager()
    animalManager = MockStrDictManager()
    visit = self.visit.clone(cageManager, animalManager, sourceManager)
    for attr in self.attributes:
      if attr != 'Nosepokes':
        self.assertEqual(getattr(visit, attr),
                         getattr(self.visit, attr))


    for nosepoke, clonedNosepoke in zip(self.visit.Nosepokes,
                                        visit.Nosepokes):
      self.assertEqual(nosepoke.sequence[-1], ('clone', sideManager, sourceManager))
      self.assertIs(clonedNosepoke._cloneOf, nosepoke)

    self.assertTrue(('getCageCorner', 4, 2) in cageManager.sequence)
    self.assertIsInstance(visit.Cage, cageManager.Cls)
    self.assertIsInstance(visit.Corner, cageManager.Cls)

    self.assertEqual(animalManager.sequence, [('get', 'animal')])
    self.assertIsInstance(visit.Animal, animalManager.Cls)

    self.assertEqual(sourceManager.sequence, [('get', 'source')])
    self.assertIsInstance(visit._source, sourceManager.Cls)

  def testReadOnly(self):
    self.checkReadOnly(self.visit)

  def testSlots(self):
    self.checkSlots(self.visit)

  def testNosepokes(self):
    for nosepoke in self.nosepokes:
      self.assertEqual(nosepoke.sequence, [('_bindToVisit', self.visit)])
      self.assertIs(nosepoke.sequence[0][1], self.visit)

  def testDel(self):
    self.checkDel(self.visit)
    for nosepoke in self.nosepokes:
      self.assertEqual(nosepoke.sequence[-1], '_del_')

  def testDuration(self):
    self.assertEqual(self.visit.Duration, timedelta(seconds=315))
    self.assertRaises(Visit.DurationCannotBeCalculatedError, lambda: self.minimalVisit.Duration)

  def testNosepokeNumber(self):
    self.assertEqual(self.visit.NosepokeNumber, 4)
    self.assertIs(self.minimalVisit.NosepokeNumber, None)

  def testNosepokeDuration(self):
    self.assertEqual(self.visit.NosepokeDuration, timedelta(seconds=102.5))
    self.assertIs(self.minimalVisit.NosepokeDuration, None)

  def testLickNumber(self):
    self.assertEqual(self.visit.LickNumber, 6)
    self.assertIs(self.minimalVisit.LickNumber, None)

  def testLickDuration(self):
    self.assertEqual(self.visit.LickDuration, timedelta(seconds=2.5))
    self.assertIs(self.minimalVisit.LickDuration, None)

  def testLickContactTime(self):
    self.assertEqual(self.visit.LickContactTime, timedelta(seconds=1.25))
    self.assertIs(self.minimalVisit.LickContactTime, None)

  def testRepr(self):
    self.assertEqual(repr(self.visit),
                     u'< Visit of "animal" to corner #2 of cage #4 (at 1970-01-01 00:00:00.000) >')


class TestNosepoke(ICNodeTest):
  attributes = ('Start', 'End', 'Side',
                'LickNumber', 'LickContactTime', 'LickDuration',
                'SideCondition', 'SideError', 'TimeError', 'ConditionError',
                'AirState', 'DoorState', 'LED1State', 'LED2State', 'LED3State',
                '_source', '_line',
                'Visit',
                )

  def setUp(self):
    self.start = datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc)
    self.end = datetime(1970, 1, 1, 0, 5, 15, tzinfo=pytz.utc)
    self.nosepoke = Nosepoke(self.start, self.end, 2,
                             2, timedelta(seconds=0.125), timedelta(seconds=0.5),
                             -1, 1, 0, 1,
                             0, 1, 0, 1, 0,
                             'src', 11)

  def testCreate(self):
    self.checkAttributes(self.nosepoke,
                         [('Start', self.start, datetime),
                          ('End', self.end, datetime),
                          ('Side', 2),
                          ('LickNumber', 2),
                          ('LickContactTime', timedelta(seconds=0.125)),
                          ('LickDuration', timedelta(seconds=0.5)),
                          ('SideCondition', -1),
                          ('SideError', 1),
                          ('TimeError', 0),
                          ('ConditionError', 1),
                          ('AirState', 0),
                          ('DoorState', 1),
                          ('LED1State', 0),
                          ('LED2State', 1),
                          ('LED3State', 0),
                          ('_source', 'src'),
                          ('_line', 11),
                         ])

  def testClone(self):
    sideManager = MockIntDictManager()
    sourceManager = MockStrDictManager()
    visit = Mock(Cage=7, Corner=1)
    self.nosepoke._bindToVisit(visit)
    nosepoke = self.nosepoke.clone(sideManager, sourceManager)
    for attr in self.attributes:
      if attr != 'Visit':
        self.assertEqual(getattr(nosepoke, attr),
                         getattr(self.nosepoke, attr))

    self.assertEqual(sideManager.sequence, [('get', 2)])
    self.assertIsInstance(nosepoke.Side, sideManager.Cls)

    self.assertEqual(sourceManager.sequence, [('get', 'src')])
    self.assertIsInstance(nosepoke._source, sourceManager.Cls)

  def testReadOnly(self):
    self.checkReadOnly(self.nosepoke)

  def testSlots(self):
    self.checkSlots(self.nosepoke)

  def testVisit(self):
    self.assertRaises(AttributeError, lambda: self.nosepoke.Visit)
    visit = object()
    self.nosepoke._bindToVisit(visit)
    self.assertIs(self.nosepoke.Visit, visit)
    self.assertRaises(AttributeError,
                      lambda: setattr(self.nosepoke, 'Visit', 12))

  def testDel(self):
    self.checkDel(self.nosepoke)

  def testDuration(self):
    self.assertEqual(self.nosepoke.Duration, timedelta(seconds=315))

  def testDoor(self):
    self.assertEqual(self.nosepoke.Door, 'right')

  def testRepr(self):
    self.assertEqual(repr(self.nosepoke),
                     u'< Nosepoke to right door (at 1970-01-01 00:00:00.000) >')

if __name__ == '__main__':
  unittest.main()