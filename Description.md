I have set of code I have developed since 2021

#  Overview
1. cda_tools2 - https://github.umn.edu/kolim/cda_tools2 

    This is the oldest set of code which I started in order to support the flexible analysis of ema survey studies.  A key feature is the concept of a proj_xyz folder which holds all the parts needed for that project.  There is a config.yaml file that specifies parameters for different steps in the analysis.  
    
    Programs such as run_parse2.py uses the config.yaml file to know how to process a hundred subjects contained in a csv file exported from Qualtrics.  The big advantage of config.yaml file is that customization to different input data is handled in the configuration file, not in modification of the  programs themselves.

    The program run_causal2.py runs the causal discovery analysis program using the java-based causal-cmd program from the tetrad package (https://github.com/cmu-phil/tetrad). A major limitation of this approach is the requirement of Java which complicates installation and usage.  This is being addressed by our tetrad-port project described below.

    There are other programs for creating different graphs and plots and also assembling summary docx files that fully document an entire analysis including config file and the output graphs and plots.

    The code is very old and does not represent best practices for code development.

2. fastcda and dgraph_flex

    https://github.com/kelvinlim/fastcda

    https://github.com/kelvinlim/dgraph_flex 

    To address some of the issues in cda_tools, I wrote the fastcda and draph_flex to support interactive use of the tools using jupyter notebooks.

    Using this approach, we can now interactively do analyses in a jupyter notebook and easily create, view and save graphs. This is really great for new users as allows one to rapidly look at analyses,  provide instant feedback and visualizations.

    It uses a jpype python to java bridge to use the code in the tetrad jar file. 

    This by far has the best and most flexible capability for plotting our graphs.

3. tetrad-port  https://github.com/kelvinlim/tetrad-port

    This is our port of tetrad 7.6.8 to C++.  We have focused on just a few causal discovery analyses and support for prior knowledge.

    It already has a python api and an R interface is also planned.

# GOAL

The ultimate goal is to have a fast, easy to install (pip install) package for conducting causal analyses.  We model this on the R graphicalVAR package (https://cran.r-project.org/web/packages/graphicalVAR/refman/graphicalVAR.html). This package is noted for ease of use which spawned its and resulted in hundred of publcations.

To accomplish this, I would like to integrate the functionality of the four listed/linked code repositories into a single unified code base.  This doesn't mean it has to be all under one repository but the key needs are:

1. command line processing

    Key for processsing large data sets (hundred cases) for individual causal modeling processing and analysis.

2. interactive jupyter notebook

    Key for interactive use and teaching.

3. Elimination of java dependency.

# Questions

1. Recommendations for how to functionally combine the packages



