# zincon

A tool that controls all your zinc files, inspired by COMP1023 Labs.  
> I heard that ZINC stands for _ZINC is not CASS_, so I guess Zincon stands for _ZINC is now CONTROLLED_  
> Btw, it's pronounced as "zinc-con", similar to the abbreviation "sing con"

## Features

- Extract a skeleton zip and initialise a working directory.
- Create a submission ZIP in one command.

## Requirements

- click

Install dependencies:

```powershell
pip install click
```

Tested on Python 3.13.7.

## Example

Basic usage: `python path\to\zincon.py`.

### zincon.py init
Initialize a skeleton from a zip:

```powershell
python .\zincon.py init path\to\skeleton.zip --out lab3
```

Or, if the skeleton zip contains `lab\d+` in its filename, you may omit `--out` and the tool will use the matched `lab\d+` as the output directory.

### zincon.py pack
Pack a submission (uses `.zincon-submit` file if present):

```powershell
python .\zincon.py pack lab3
```

You may also specify the output directory with the option `--out`, relative to the working directory. Otherwise, the tool will create a `submission.zip` under the working directory.

## Contributing

Contribution is welcome. However, please note that the original intention of this tool is to improve my own zinc workflow, so the tool is customized to my own needs. Please open an issue or PR with a clear description if applicable.
