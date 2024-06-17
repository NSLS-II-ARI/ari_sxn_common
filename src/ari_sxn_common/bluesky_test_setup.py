""" This file is used to setup a bluesky session with standard items"""
from ari_ophyd import M1
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.plans import count, scan, grid_scan
from bluesky.utils import ProgressBarManager
from databroker import Broker

# Create run engine
RE = RunEngine({})
# Add best effort callback (tables, plotting, ...)
bec = BestEffortCallback()
RE.subscribe(bec)
# Add a temporary databroker
db = Broker.named('temp')
RE.subscribe(db.insert)
# Add Progress bars
RE.waiting_hook = ProgressBarManager()

# Setup the m1 mirror ophyd object
m1_locations_data = {'measure': {'diag.locations': ('Out', None),
                                 'slits.locations': ('nominal', None)},
                     'Yag': {'diag.locations': ('YaG', None),
                             'slits.locations': ('nominal', None)}}
m1 = M1('ARI_M1:', name='m1', locations_data=m1_locations_data,
        labels=('device',))
