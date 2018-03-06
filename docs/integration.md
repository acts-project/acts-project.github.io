# <a name="integration">Integration</a>

## Technical integration

In order to use ACTS in your project, you need to integrate it in you build.
Currently, onluy `CMake` based builds are supported.

## Customizing ACTS

ACTS comes with several possibilities of customisation in order to allow a seamless integration in the experminet software.

### <a name="integration_output">Screen output logging</a>

A default screen logging system is integrated in ACTS, but can be overloaded with the experiment's logging system.
 
### Plugins at compile time

Several plugins of ACTS can be set by compile time, these are header-only files that exchange the 
default implementations of ACTS.

#### Change of parameter definition

This can be done by providing the different parameter definition file and declaring it as

    ACTS_PARAMETER_DEFINITIONS_PLUGIN='<path_to>/<filename.hpp>'

*TODO:* Write a CI test for this

#### Change of `Identifier` class 

The Identifier class can be exchanged by declareing:

    ACTS_CORE_IDENTIFIER_PLUGIN

*TODO:* Write a CI test for this, together with Identifier change

#### <a name="integration_bField">Interfacing with magnetic field</a> 

The magnetic field integration is done using a `concept` implementation that is designed for 
field cell caching. The propagation modules take the magentic field as a template argument,
hence providing the correct concept guarantess compatibility with ACTS.

### System of Units

ACTS uses a set of system of units and its interanl code tries to minimise unit conversions,
however, when converting into the ACTS data model, this should be done using the ACTS units

Internally, ACTS uses a set of `SI2Nat<>` template funtion to free the code from conversion 
constants.

    /// @brief physical quantities for selecting right conversion function
    enum Quantity { MOMENTUM, ENERGY, LENGTH, MASS };
    
    /// @cond
    template <Quantity>
    double
    SI2Nat(const double);
    
    template <Quantity>
    double
    Nat2SI(const double);


*TODO:* Write a unit test for this, investigate if we can do this as a `PLUGIN` as well 

## <a name="integration_configuration">Configuration</a>

ACTS does not come with a dedicated configuration system to bind to any experiments software.
Instead, a simple decision has been taken to equip every configurable component of ACTS with a
nested `Config` struct.

This struct object is used to construct the according ACTS tool, e.g.

    class CylinderVolumeBuilder : public ITrackingVolumeBuilder
    {
    public:
      /// @struct Config
      /// Nested configuration struct for this CylinderVolumeBuilder
      struct Config
      {
        /// the trackign volume helper for construction
        std::shared_ptr<const ITrackingVolumeHelper> trackingVolumeHelper = nullptr;
        /// the string based indenfication
        std::string volumeName = "";
        /// The dimensions of the manually created world
        std::vector<double> volumeDimension = {};
        /// the world material
        std::shared_ptr<const Material> volumeMaterial = nullptr;
        /// build the volume to the beam line
        bool buildToRadiusZero = false;
        /// needed to build layers within the volume
        std::shared_ptr<const ILayerBuilder> layerBuilder = nullptr;
        /// the envelope covering the potential layers rMin, rMax
        std::pair<double, double> layerEnvelopeR
            = {1. * Acts::units::_mm, 1. * Acts::units::_mm};
        /// the envelope covering the potential layers inner/outer
        double layerEnvelopeZ = 10. * Acts::units::_mm;
        /// the volume signature
        int volumeSignature = -1;
      };

To configure ACTS tools, thus, one has to guarantee that necessary configuration parameters are forwarded through the framework configuration mechanism.



