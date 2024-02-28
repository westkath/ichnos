# Carbon-Footprint
A project with scripts to methodically calculate the Carbon Footprint of Workflow Executions from Nextflow trace files.

# Usage
For the initial version, replicating the previous calculation approach noted in the Credits section, example usage has been provided with default values:
```
$ python -m src.scripts.CarbonFootprint <trace-file-name> <carbon-intensity> <power-usage-effectiveness> <cpu-power-draw> <memory-power-draw> <config-profile>"  
$ python -m src.scripts.CarbonFootprint test 475 1.67 12 0.3725 default
```  
Note that the trace file name must be the file name only, and traces should be csv files stored in the [data trace](data/trace/) directory!  
Configuration Profiles are available and can be adjusted - see the [trace config](config/trace.conf) - default refers to a csv file.   
Future plans will look at using CI values based on the time interval that the trace was executed in, and inclusion of variable cpu and memory power draw values. 

# Output
The script will produce two files. If the trace file name was 'test', then 'test-trace.csv' would produce a csv file of Carbon Records with energy consumption (inc. PUE) and carbon footprint for each task in the trace file. The 'test-summary.txt' file will contain details around the provided parameters (e.g. CI, PUE) and the overall energy, memory and carbon footprint.     
See the [test-summary](output/test-summary.txt) and [test-trace](output/test-trace.csv). 

# Credits
- [Carbon Footprint](src/scripts/CarbonFootprint.py) is adapted from the [nf-co2footprint](https://github.com/nextflow-io/nf-co2footprint) plugin which was based on the carbon footprint computation method developed in the [Green Algorithms](https://www.green-algorithms.org/) project. 
  > **Green Algorithms: Quantifying the Carbon Footprint of Computation.**
  > Lannelongue, L., Grealey, J., Inouye, M.,
  > Adv. Sci. 2021, 2100707. https://doi.org/10.1002/advs.202100707
- [Carbon Intensity](src/scripts/CarbonIntensity.py) makes use of the [Carbon Intensity API](https://carbonintensity.org.uk/).
- [Nextflow Trace Files](data/trace/) are generated from [Nextflow]() workflow executions. 
  > **Nextflow enables reproducible computational workflows**
  > P. Di Tommaso, M. Chatzou, E. W. Floden, P. P. Barja, E. Palumbo, and C. Notredame,
  > Nature Biotechnology, vol. 35, no. 4, pp. 316–319, Apr. 2017, https://doi.org/10.1038/nbt.3820