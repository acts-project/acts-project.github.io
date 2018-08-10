# Developer Guidelines for Acts


## Writing thread-safe code

Acts aims to be readily usable from multi-threaded event reconstruction frameworks. To achieve this goal, all internal Acts state should either be kept private to a thread or remain constant after initialization. This is supported by aiming at a strict discipline of const-correctness (i.e. data reached via a const pointer cannot be mutated), the only allowed exceptions being deferred initialization code which does not run in parallel such as the geometry building process.

### Const correctness

Very simple rules for `const` correctness should be followed by convention. As every tool that performs an operation is permitted to have a internal state, every method has to be declared `const` as it is not allowed to alter the sate of the exectuing tool.
    
```cpp
/// Method that performs an operation
/// 
/// @param input variable that is needed by this method
/// 
/// @return a direct output of this method
return_type doSomethingWithoutCache(const input_type& input) const; 
```

### Stateless tools and visitor cache

It is indeed sometimes useful and needed to cache certain values or parameters for repetitive use. For example, track propagation requires access to the detector's magnetic field, which can be sped up by caching intermediary computations across extrapolation steps.

Any tool in Acts that requires a cache must follow a visitor pattern design, i.e. the caller provides the cache in the function call and thus guarantees that the cache is thread-local. The ``Cache`` struct has to be done as a nested struct of the class and is being called as such. As a convention, the cache object is usually the first one provided in the method signature as a `Cache&`

```cpp
/// An Acts Tool that does some well defined job
class MyTool {
  public:
  /// Cache for Acts tool
  ///
  /// it is exposed to public for use of the expert-only
  /// propagate_with_cache method of the propagator
  struct Cache
  {
    variable_type var; ///< the local cache 
  }
  
  /// Method that performs an operation and also relies on a cache
  /// 
  /// @param cache object
  /// @param input variable that is needed by this method
  /// 
  /// @return a direct output of this method
  return_type doSomethingWithCache(Cache& cachem, const input_type& input) const; 
  
};
```
  

## Configuration of Acts tools

Configuration in Acts is done via a dedicated nested configuration struct which then is used for constructing the tool itself. By convention, this struct is called `Config`.

```cpp
/// An Acts Tool that does some well defined job
class MyTool {
  public:
  /// Configuration struct
  struct Config {
    variable_type parameter;
  };
  
  /// Tool constructor
  /// 
  /// @param cfg is the configuration struct
  MyTool(const Config&cfg) : m_cfg(cfg){}
   
  private:
    Config m_cfg; ///< the configuration object
};
```

This `Config` object can then be used to create and configure the tool. In case Acts is embedded in an experiment framework,
the `Config` public members have to be connected to the framework configuration.

```cpp
// Create a config object and set my configuration parameter
MyTool::Config mtConfig;
mtConig.parameter = 3.1415927;

// Now create a tool with this configuration
MyTool mt(mtConfig);
```
    
