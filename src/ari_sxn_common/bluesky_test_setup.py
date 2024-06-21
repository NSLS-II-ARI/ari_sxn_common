""" This file is used to setup a bluesky session with standard items"""
from ari_ophyd import M1
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky import plans as plans
from bluesky import plan_stubs as plan_stubs
from bluesky.utils import ProgressBarManager
import common_bluesky
from databroker import Broker
from ophyd.signal import EpicsSignalBase

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

EpicsSignalBase.set_defaults(timeout=10, connection_timeout=10)

# create the plan_stub objects
for plan_stub, aliases in common_bluesky._plan_stubs_to_import.items():
    for alias in aliases:
        globals()[alias] = getattr(plan_stubs, plan_stub)
# create the plan objects
for plan, aliases in common_bluesky._plans_to_import.items():
    for alias in aliases:
        globals()[alias] = getattr(plans, plan)

# Setup the m1 mirror ophyd object
m1_locations_data = {'measure': {'diag.locations': ('Out', None),
                                 'slits.locations': ('nominal', None)},
                     'Yag': {'diag.locations': ('YaG', None),
                             'slits.locations': ('nominal', None)}}
m1 = M1('ARI_M1:', name='m1', locations_data=m1_locations_data,
        labels=('device',))

plans = common_bluesky.PlanCollector(
    plans_to_import=common_bluesky._plans_to_import,
    plan_stubs_to_import=common_bluesky._plan_stubs_to_import)
