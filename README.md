# Conky-maker READ-ME

## Introduction

Conky-maker has a script that generates Conky configurations. It seeks to
provide the following benefits, particularly when compared to writing raw Conky
configurations.

* It separates system data from design to allow one design to produce different
  results for different target systems.
* A clean JSON or YAML data format is used for describing system environments.
* Design modules have clean and compact Python code to generate configurations.
* A "conky" library provides a simpler way to compose complex '$' commands.
* The library provides some higher level functions to hide the complexity of
  using various external commands, e.g. to get the external IP address.
* The library supports IDEs, including VSCode and PyCharm. It enables automatic
  prompting for configuration item parameters, with full typing information.

## Requirements

Either the "json" or "yaml" library must be available to Python for import,
depending on the format used for system configurations.

Both JSON and YAML formats are supported and detected. Detection is primarily
based on the file extension, i.e. ".yaml" or ".json", and falls back to content
inspection if an unexpected extension is received. The program picks JSON if the
first non-whitespace character is '{'.

Note that only the "json" or "yaml" library module that is needed for the run
gets imported. There will not be an error if the other support library is not
available locally. For example, there will not be an error if the data file is
JSON format and the system interpreter has no YAML support.

## Usage

It has the following simple two argument interface.

```
./conky.py DATA_FILE DESIGN_FILE
```

DATA_FILE is a path to a JSON or YAML file, typically taken from the "data"
folder. It describes the system environment and a set of devices to monitor.

DESIGN_FILE is a Python module path, typically taken from the "design" folder.
It implements a Conky configuration generator. Design modules produce Conky
desktop widgets with different appearances and content.

The maker script writes the resulting Conky configuration to stdout. To use the
results with Conky redirect the output to a file, e.g. "conky.conf".

The conky.py program provides online help through the -h or --help options. But
for now it is not very useful.
