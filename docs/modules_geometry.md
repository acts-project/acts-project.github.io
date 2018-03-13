# Geometry module

The ACTS geometry model is strongly based on the ATLAS Tracking geometry. Its core is built on a surface-based description that make up all geometry objects of higher complexity. This design has been chosen as the surface objects can be used together with the track propagation module and thus all geometry objects become natively integrated into the tracking software.

## Identifier

ACTS uses an identification scheme, in which objects can be assigned a unique identifier. The concrete implementation of the identifier can be provided by the client code. This is done through the `Identifier` class used in ACTS, which can be changed at compile time to be the Identifier class of the experiment. This can be done using the `ACTS_CORE_IDENTIFIER_PLUGIN` before compiling ACTS:

```cpp
#ifdef ACTS_CORE_IDENTIFIER_PLUGIN
#include ACTS_CORE_IDENTIFIER_PLUGIN
#else

#define IDENTIFIER_TYPE unsigned long long
#define IDENTIFIER_DIFF_TYPE long long

#include <string>

/// @class Identifier
///
/// minimum implementation of an Identifier,
/// please use the ACTS_CORE_IDENTIFIER_PLUGIN in to use instead if
/// another type of Identifier is needed
///
class Identifier
{
// ...
};
```

There are very little constraints on the Identifier class, it has to be 

    * default constructable
    * copy constructable
    * move constructable 
    * assignment operator being defined
    

For compatibility with the ATLAS software, 
an `is_valid()` method has to be implemented:

     /// Check if id is in a valid state
      bool is_valid () const;

Other than that, ACTS imposes no requirement on the  `Identifier` class.

*QUESTION:*: Can we change this in ATLAS SW to an `operator bool()` ?


## GeometryObject base class and GeometryID

All geometry objects in ACTS inherit from a virtual `GeometryObject` base class

    /// @class GeometryObject
    ///
    /// Base class to provide GeometryID interface:
    /// - simple set and get
    ///
    /// It also provides the binningPosition method for
    /// Geometry geometrical object to be binned in BinnedArrays
    ///
    class GeometryObject
    {
    public:
     /// default constructor
     GeometryObject() : m_geoID(0) {}
    
     /// constructor from a ready-made value
     ///
     /// @param geoID the geometry identifier of the object
     GeometryObject(const GeometryID& geoID) : m_geoID(geoID) {}
    
     /// assignment operator
     ///
     /// @param geoID the source geoID
     GeometryObject&
     operator=(const GeometryObject& geoID)
     {
       if (&geoID != this) m_geoID = geoID.m_geoID;
       return *this;
     }
    
     /// Return the value
     /// @return the geometry id by reference
     const GeometryID&
     geoID() const;
    
     /// Force a binning position method
     ///
     /// @param bValue is the value in which you want to bin
     ///
     /// @return vector 3D used for the binning schema
     virtual const Vector3D
     binningPosition(BinningValue bValue) const = 0;
    
     /// Implement the binningValue
     ///
     /// @param bValue is the dobule in which you want to bin
     ///
     /// @return float to be used for the binning schema
     double
     binningPositionValue(BinningValue bValue) const;
    
     /// Set the value
     ///
     /// @param geoID the geometry identifier to be assigned
     void
     assignGeoID(const GeometryID& geoID);
    
    protected:
     GeometryID m_geoID;
    };

This class ensures that a unique `GeometryID` is assigned to every geoemtry object. The `GeometryID` is mainly used for fast identification of the type of the geometry object (as most are either extensions or containers of the `Surface` objects) and for
the identification of the geometery surfaces after building, e.g. for the uploading/assigning of material to the surface after creation. The `GeometryID` uses a simple masking procedure for applying an identification schema.

It is used for ACTS internal applications, such as material mapping, but not for `EventData` and `Geometry` identification in an experiment setup, for this the `Identifier` class is to be used and/or defined.

    typedef uint64_t geo_id_value;
    
    namespace Acts {
    
    /// @class GeometryID
    ///
    ///  Identifier for Geometry nodes - packing the
    ///  - (Sensitive) Surfaces    - uses counting through sensitive surfaces
    ///  - (Approach)  Surfaces    - uses counting approach surfaces
    ///  - (Layer)     Surfaces    - uses counting confined layers
    ///  - (Boundary)  Surfaces    - uses counting through boundary surfaces
    ///  - Volumes                 - uses counting given by TrackingGeometry

    class GeometryID
    {
    
    public:
      const static geo_id_value volume_mask    = 0xff00000000000000;
      const static geo_id_value boundary_mask  = 0x00ff000000000000;
      const static geo_id_value layer_mask     = 0x0000ff0000000000;
      const static geo_id_value approach_mask  = 0x000000f000000000;
      const static geo_id_value sensitive_mask = 0x0000000ffff00000;
      const static geo_id_value channel_mask   = 0x00000000000fffff;
    
      ...
    };
        

## Surface classes

The `Surface` class builds the core class of all geometry objects and can be used natively with the propagation and extrapolation modules. The common `Surface` virtual base defines the public interface of all surfaces. 

## Layer classes

The `Layer` class is an extension of the `Surface` class that allows the definition of sub surfaces (sensitive surfaces for modules, or extra material surfaces).

## Volume description

<!--The `Volume` class is a container of `BoundarySurface` objects, where each `BoundarySurface` is an -->

## Building procedure and volume 'glueing'

The geometry building procedure follows the ATLAS TrackingGeometry philosophy of a static frame of *glued* volumes,
that lead the navigation flow through the geometry, 


## Material description

### Material mapping from Geant4

