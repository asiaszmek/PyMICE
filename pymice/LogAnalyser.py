#!/usr/bin/env python
# encoding: utf-8
"""
LogAnalyser.py

Created by Szymon Łęski on 2013-01-21.
Refactored by Jakub Kowalski on 2015-02-20.

Copyright (c) 2012-2015 Laboratory of Neuroinformatics. All rights reserved.
"""
import time
from datetime import datetime
from pytz import UTC
from math import ceil
import collections

import numpy as np
import matplotlib.mlab as mmlab

from ._Tools import toTimestampUTC

class ExcludeMiceData(object):
  """
  A class for storing information about excluded data segments / modalities
  """
  def __init__(self, startTime=0., endTime=0., logType=None, notes=None, **kwargs):
    self.startTime = startTime
    self.endTime = endTime
    self.logType = logType
    # logtype should be one of: Lickometer, Presence, Corner, Cage, SocialBox,
    # AnimalGate, ???
    self.notes = notes

    # The rest of the fields goes to the location dictionary
    self.location = {}
    for key in ['cage', 'corner', 'side']:
      self.location[key] = kwargs.pop(key, None)

    self.location.update(kwargs)

  def __repr__(self):
    ss = 'Exclude %s from %s to %s\nin location: %s.'\
          % (self.logType,
             self.startTime.strftime("%Y-%m-%d %H:%M:%S.%f"),
             self.endTime.strftime("%Y-%m-%d %H:%M:%S.%f"),
             ', '.join('%s = %s' % x for x in self.location.items()),)
    if self.notes is not None:
      ss += '\n\nNotes:\n' + self.notes

    return ss


class ILogAnalyzer(object):
  def __call__(self, md):
    raise NotImplementedError("Virtual method called")

class LickometerLogAnalyzer(ILogAnalyzer):
  def __init__(self, shortThreshold=3, medThreshold=None):
    self.shortThreshold = shortThreshold
    self.medThreshold = 4 * shortThreshold if medThreshold is None else medThreshold

    self.medBin = 3600. # 1-hour bins for final processing
    self.shortBin = 900.
    self.notes = '\n'.join(['Generated by LickometerLogAnalyzer with ',
                          'shortThreshold = %3.2f, medThreshold = %3.2f'
                          %(self.shortThreshold, self.medThreshold), '', ''])

  def __call__(self, md):
    # TODO Make sure we do not get strange starting and ending times
    # resulting from strange bins
    results = []
    log = md.getLog()
    for cage in md.getInmates():
      for side in range(1, 9):
        tt = np.array([toTimestampUTC(l.DateTime) for l in log \
                       if l.Type == 'Lickometer' and l.Cage == cage and l.Side == side])
        if len(tt) > 0:
          ttMin = tt.min()
          span = tt.max() - ttMin
          nBins = ceil(span / self.medBin)
          medBins = np.linspace(ttMin, ttMin + nBins * self.medBin, int(nBins) + 1)
          medHist, _ = np.histogram(tt, bins=medBins)
          # short_bins = np.arange(tt.min(), tt.max()
          #              + self.short_bin, self.short_bin)
          # short_hist = np.histogram(tt, bins=short_bins)[0]
          if (medHist > self.medThreshold).any():
            # or np.all(short_hist > self.threshold_short):
            pass
            idcs = mmlab.contiguous_regions(medHist > self.medThreshold)
            # print idcs
            for tstartidx, tstopidx in idcs:
              tstart = medBins[tstartidx]
              tstop = medBins[tstopidx]
              # print tstart, tstop
              results.append(ExcludeMiceData(startTime=datetime.fromtimestamp(tstart, UTC),
                      endTime=datetime.fromtimestamp(tstop, UTC), logType='Lickometer',
                      cage=cage, side=side,
                      notes=str(sum(medHist[tstartidx:tstopidx]))
                      + ' cases. ' + self.notes))

    return results

class OldLogAnalyzer(ILogAnalyzer):
  """Moved here from miceloader2, just prints warnings and errors"""
  def __call__(self, md):
    log = md.getLog()
    errors = [l for l in log if l.Category  == 'Error' and l.Type not in ('Lickometer', 'Nosepoke')]

    if len(errors) > 0:
      print '%d errors' % len(errors)

    warnings = [l for l in log if l.Notes.startswith('Unregistered tag') or l.Notes.startswith('Presence signal')]

    if len(warnings) > 0:
      print '%d warnings in logs' % len(warnings)
      notes = collections.Counter(l.Notes for l in warnings)
      for note, n in sorted(notes.items()):
        print "%s: %d time(s)" % (note, n)

    return () #dummy return to keep _logAnalysis happy


class PresenceLogAnalyzer(ILogAnalyzer):
  """Analyze 'presence' errors"""
  def __init__(self):
    self.notes = '\n'.join(['Generated by PresenceLogAnalyzer', '', ''])
    self.finBin = 3600. # Final bins: 1 hour

  def __call__(self, md):
    results = []
    log = md.getLog(order='DateTime')
    for cage in md.getInmates():
      for corner in range(1, 5):
        tt = np.array([toTimestampUTC(l.DateTime) for l in log \
                       if l.Cage == cage and l.Corner == corner and l.Notes.startswith('Presence signal')])
        if len(tt) > 0:
          # print cage, corner, len(events)
          ttOrig = tt.copy()
          tds = np.diff(tt)

          # # Wywalanie jesli sa co najmniej 3 w czasie ponizej minuty
          # idcs = np.zeros_like(tt)
          # for idx, there, dthere in zip(range(len(tt)-1), tt[:-1], tds):
          #     if dthere < 60.:
          #         # print idx, there, dthere
          #         idx2 = np.where((tt >= there)&(tt < there + 60.))[0]
          #         # print idx, idx2
          #         if len(idx2) >= 3:
          #             idcs[idx2] = 1
          # print idcs
          # tt = np.delete(tt, np.where(idcs))

          # Wywalamy blizsze siebie niz 30 s
          idcs = np.zeros_like(tt)
          idcs[tds < 30.] = 1
          tds = np.r_[np.nan, tds]
          idcs[tds < 30.] = 1
          tt = np.delete(tt, np.where(idcs))

          if len(tt) > 0:
            # Wywalamy jesli izolowany
            tds = np.diff(tt)
            idcs = np.zeros_like(tt)
            idcs[0] += 0.5
            idcs[-1] += 0.5
            idcs[tds > 1800.] += 0.5
            tds = np.r_[np.nan, tds]
            idcs[tds > 1800.] += 0.5
            tt = np.delete(tt, np.where(idcs > 0.75))

          if len(tt) > 0:
            # Pomijamy jesli <= 4 bledy w dobie
            ttMin = tt.min()
            span = tt.max() - ttMin
            nBins = ceil(span / (24 * 3600.))
            longBins = np.linspace(ttMin, ttMin + nBins * 24 * 3600.,
                                   int(nBins) + 1)
            hist, _ = np.histogram(tt, bins=longBins)
            if np.all(hist > 4).any():
              # print cage, corner, 'Zostalo ', len(tt)
              nBins = ceil(span / self.finBin)
              bins = np.arange(ttMin, ttMin + nBins * self.finBin,
                               int(nBins) + 1)
              hist, _ = np.histogram(tt, bins=bins)
              idcs = mmlab.contiguous_regions(hist)
              for tstartidx, tstopidx in idcs:
                tstart = bins[tstartidx]
                tstop = bins[tstopidx]
                results.append(ExcludeMiceData(startTime=datetime.fromtimestamp(tstart, UTC),
                        endTime=datetime.fromtimestamp(tstop, UTC),
                        logType='Presence',
                        cage=cage, corner=corner,
                        notes=str(sum(hist[tstartidx:tstopidx]))
                        + ' cases. ' + self.notes))

    return results


def overlap(exc, interval):
  """
  Check whether the time interval definded in exc
  (exc.startTime to exc.endTime) has non-zero overlap
  with time interval given as the second argument.
  """
  start, end = interval
  return start <= exc.startTime < end or\
         start < exc.endTime <= end or\
         exc.startTime <= start and exc.endTime >= end


class ITestMiceData(object):
  def __call__(self, md, timeinterval, **kwargs):
    raise NotImplementedError("Virtual method called")

  def _single_test(self, exc, timeinterval, **kwargs):
    raise NotImplementedError("Virtual method called")


class TestMiceData(ITestMiceData):
  def __init__(self, logType=None):
    if logType is not None:
      self._logType = logType

  def __call__(self, md, interval, **kwargs):
    result = True
    for exc in md.getExcluded():
      if not self._single_test(exc, interval, **kwargs):
        return False

    return True

  def _single_test(self, exc, interval, **kwargs):
    """
    Perform a test on a single ExcludeMiceData object
    """
    if exc.logType is self._logType and overlap(exc, interval):
      for key, value in kwargs.items():
        try:
          if value != exc.location[key]:
            return True

        except KeyError:
          pass

      return False

    return True


class TestLickometer(TestMiceData):
  """
  Test whether lickometer data can be analyzed. Return True
  if no errors, False if data should be excluded.
  Location conditions to be checked can be passed in kwargs, eg.:
  cage='5' will check for exc.location['cage'] == '5'
  """
  _logType = 'Lickometer'
  #def _single_test(self, exc, interval, **kwargs):
  #  """
  #  Perform Lickometer test on a single ExcludeMiceData object
  #  """
  #  result = True
  #  if exc.logType is "Lickometer":
  #    if overlap(exc, interval):
  #      result = False
  #      for key in kwargs:
  #        try:
  #          if kwargs[key] != exc.location[key]:
  #            result = True

  #        except KeyError:
  #          pass

  #      if not result:
  #        return False

  #  return result


class TestPresence(TestMiceData):
  """
  Test for data excluded due to 'Presence' errors. Return True
  if no errors, False if data should be excluded.
  Location conditions to be checked can be passed in kwargs, eg.:
  cage='5' will check for exc.location['cage'] == '5'
  """
  _logType = 'Presence'
  #def _single_test(self, exc, interval, **kwargs):
  #  result = True
  #  if exc.logType is "Presence":
  #    if overlap(exc, interval):
  #      result = False
  #      for key in kwargs:
  #        try:
  #          if kwargs[key] != exc.location[key]:
  #            result = True

  #        except KeyError:
  #          pass

  #      if not result:
  #        return False

  #  return result
