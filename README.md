# Carbon-Footprint
A project with scripts to methodically calculate the Carbon Footprint of Workflow Executions from Nextflow trace files.

# Credits
- [Carbon Footprint](scripts/CarbonFootprint.py) is adapted from the [nf-co2footprint](https://github.com/nextflow-io/nf-co2footprint) plugin which was based on the carbon footprint computation method developed in the [Green Algorithms](https://www.green-algorithms.org/) project. 
  > **Green Algorithms: Quantifying the Carbon Footprint of Computation.**
  > Lannelongue, L., Grealey, J., Inouye, M.,
  > Adv. Sci. 2021, 2100707. https://doi.org/10.1002/advs.202100707
- [Carbon Intensity](scripts/CarbonIntensity.py) makes use of the [Carbon Intensity API](https://carbonintensity.org.uk/).
- [Nextflow Trace Files](data/trace/) are generated from [Nextflow]() workflow executions. 
  > **Nextflow enables reproducible computational workflows**
  > P. Di Tommaso, M. Chatzou, E. W. Floden, P. P. Barja, E. Palumbo, and C. Notredame,
  > Nature Biotechnology, vol. 35, no. 4, pp. 316–319, Apr. 2017, 10.1038/nbt.3820