# FlexDriver performance and memory utilization models

This repository includes the notebooks for calculating memory utilization
and performance model for paper *FlexDriver: A Network Driver for Your Accelerator*.

The contents include:

- [fld_model.py](fld_model.py) - Python module of the performance model for FlexDriver.
- [fld_model_figures.ipynb](fld_model_figures.ipynb) - Jupyter notebook to run the performance model and chart the results.
- [mem_usage.ipynb](mem_usage.ipynb) - Jupyter notebook with memory utilization computation for both CPU drivers and FlexDriver.

## How to run

Install anaconda from https://www.anaconda.com/, and create an environment:

    conda env create --name fld-model --file conda.yaml

Run jupyter:

    conda activate fld-model
    jupyter notebook

and open the desired notebook.