# Developer Guidelines for ACTS


## Writing thread-safe code

ACTS aims to prepare a track reconstruction toolkit ready for concurrent use, hence it is important to keep stick to some guidelines.
A few exceptions of const correct and stateless code is still present in the geometry building process, which - however - is not being executed in a parallel manner.

### Const correctness

Very simple rules for `const` correctness should be followed by convention. As every tool that performs an operation is permitted to have a internal state, every method has to be declared `const` as it is not allowed to alter the sate of the exectuing tool.
    
      /// Method that performs an operation
      /// 
      /// @param input variable that is needed by this method
      /// 
      /// @return a direct output of this method
      return_type doSomethingWithoutCache(const input_type& input) const; 
    
The return type does not need to be `const`, though should be declared `const` if no modification of the returned object is foreseen.   

### Stateless tools and visitor cache

It is indeed sometimes useful and needed to cache certain values or parameters for repetitive use. One of these usecases is e.g. the propagation through the magnetic field, where caching the field value from the current field cell can help to improve the CPU performance, as retrieving the field values from memory is - when beeing performed very often - of significant time.

Any tool in ACTS that requires a cache must follow a visitor pattern design, i.e. the caller provides the cache in the function call and thus guarantees that the cache is thread-local. The ``Cache`` struct has to be done as a nested struct of the class and is being called as such. As a convetion, the cache object is usually the first one provided in the method signature as a `Cache&`

    /// An ACTS Tool that does some well defined job
    class MyTool {
      public:
      /// Cache for ACTS tool
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
  

## Configuration of ACTS tools

Configuration in ACTS is done via a dedicated nested configuration struct which then is used for constructing the tool itself. By convention, this struct is called `Config`.

    /// An ACTS Tool that does some well defined job
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

This `Config` object can then be used to create and configure the tool. In case ACTS is embedded in an experiment framework,
the `Config` public members have to be connected to the framework configuration.

    // Create a config object and set my configuration parameter
    MyTool::Config mtConfig;
    mtConig.parameter = 3.1415927;
    
    // Now create a tool with this configuration
    MyTool mt(mtConfig);
    
    
