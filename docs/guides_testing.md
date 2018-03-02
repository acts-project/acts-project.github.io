# ACTS tests and continuous integration

Modern software development techniques relies on automated tests and
continuous integration platforms to ensure the functionality of a given
software package. It verifies that existing behaviour remains unchanged
when updating or optimizing its implementation and allows automated
testing of new functionality.

ACTS provides an extensive unit test suite that checks geometry and
propagation functionality at the smallest unit level, e.g. a single
geometric surface type. Tests are based on known solutions for simple
cases or manual calculations for selected configuration. These tests can
be run very fast and usually take less that a second. They allow fast
iteration and verification for the developers.

In addition, we have started to provide larger integration tests that
aim to test combinations of multiple ACTS components. A typical example
would be a full geometry propagation chain. It includes geometry
description, geometry navigation, and particle propagation that all have
to work together to allow efficient transport of particles through a
tracking detector. The integration tests usually check for
self-consistency or variations from previous known-good results for a
large variety of inputs. They are expected to have a run time of the
order of minutes and are intended to run as part of a merge request.

ACTS employs the continuous integration platform provided by the CERN
Gitlab installation. Within this platform each change pushed to the
common repository is compiled with multiple build configurations.  The
build configuration are chosen to encompass all supported Linux
distributions (Scientific Linux CERN 6, CERN CentOS 7), different
compilers (GCC, CLang) and different LCG software releases starting from
the minimum requirement (LCG91). Additional checks are performed to
ensure consistent licensing and formatting. The available platforms were
chosen to be consistent with typical setups available to users, e.g. on
lxplus machines at CERN. Special care was taken to not require any
additional software but the ones provided by the distributions
themselves and the LCG releases with the versions that are provided. The
continuous integration builds activate all optional components to avoid
unintentional breakage due to deactivated components on a developers
local copy. Together ensures consistent functionality and ease-of-use on
all platforms and greatly reduces possible barriers for future users.
    