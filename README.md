# zincon

A tool that controls all your zinc files, inspired by COMP1023 Labs.  
Testing currently works for **Python** lab/PAs only. You may modify testing scripts in `_run_test_case()` to match your need.  
> I heard that ZINC stands for _ZINC is not CASS_, so I guess Zincon stands for _ZINC is now CONTROLLED_  
> Btw, it's pronounced as "zinc-con", similar to the abbreviation "sing con"

## Features

- Extract a skeleton zip and initialize a working directory.
- Create a submission ZIP in one command.
- Run all test cases and show diff locally.

## Installation

You may install zincon by cloning this repository, then running the following commands, preferably under a **virtual environment**:
```sh
cd path\to\zincon 
pip install -e .
``` 
Then you may run `zincon` directly in your environment.

If you wish to use zincon without installing, replace `zincon` with `python path\to\zincon.py` in your commands.

## Requirements

If you do not wish to install zincon directly, you will need to install the requirements manually.  
**If you have successfully installed zincon using `pip install -e .`, you can skip this part.**

### Required packages
- click

### Install dependencies:

```powershell
pip install click
```

Tested on Python 3.13.7.

## Example

### zincon init \<skeleton_path>
Initialize a skeleton from a zip:

```powershell
zincon init path\to\skeleton.zip --out lab3
```

Or, if the skeleton zip contains `lab\d+` in its filename, you may omit `--out` and the tool will use the matched `lab\d+` as the output directory.

Example output structure:
```
lab0
│  .zincon-submit
│  lab0_skeleton.py
├─backup
│  │  lab0_skeleton.py
│  └─testcases
│          input01.txt
│          output01.txt
└─testcases
        input01.txt
        output01.txt
```

### zincon pack \<path>
Pack a submission (uses `.zincon-submit` file if present):

```powershell
zincon pack lab3
```

You may also specify the output directory with the option `--out`, relative to the working directory. Otherwise, the tool will create a `submission.zip` under the working directory.

### zincon test \<path> \<entrypoint> [<testcases_dir>]
Run testcases on current progress.

```powershell
zincon test lab3 <lab3_entrypoint>.py
```

Specify testcase filename formats by `--ifmt` and `--ofmt`. Defaults to `input{}.txt` and `output{}.txt`.  
Override default timeout of 30s using `--timeout`.  

## Contributing

Contribution is welcome. However, please note that the original intention of this tool is to improve my own zinc workflow, so the tool is customized to my own needs. Please open an issue or PR with a clear description if applicable.
