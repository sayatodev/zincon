import os
import click
import re
import shutil
from zipfile import ZipFile

@click.group()
def cli():
    pass

@cli.command()
@click.argument('skeleton_path', required=True)
@click.option('--out', '-o', help="Output directory", default=None, type=click.Path())
@click.option('--recursive-backup', default=True, is_flag=True, help="Enable recursive backup of existing files")
def init(skeleton_path, out, recursive_backup):
    if out is None:
        match = re.search(r'lab\d+', skeleton_path)
        if match:
            out = f"./{match.group(0)}"
        else:
            out = f"./{skeleton_path.rsplit('.', 1)[0]}"
            
    # Check if output directory exists, prompt for confirmation
    if os.path.exists(out):
        click.confirm(f"The directory {out} already exists. Do you want to overwrite it?", abort=True)
        shutil.rmtree(out)

    tmp_dir = os.path.join(out, "../.zincon_tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    with ZipFile(skeleton_path, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    files = os.listdir(tmp_dir)

    # if the zip contains a single top-level directory, move its contents up
    if len(files) == 1 and os.path.isdir(os.path.join(tmp_dir, files[0])):
        tld = os.path.join(tmp_dir, files[0])
        for item in os.listdir(tld):
            os.rename(
                os.path.join(tld, item),
                os.path.join(tmp_dir, item)
            )

    # backup existing files
    skeleton_files = os.listdir(tmp_dir)
    backup_dir = os.path.join(tmp_dir, "backup")
    if recursive_backup:
        shutil.copytree(tmp_dir, backup_dir, dirs_exist_ok=True)
    else:
        for file in skeleton_files:
            src = os.path.join(tmp_dir, file)
            shutil.copyfile(src, os.path.join(backup_dir, file))
            
    # create .zincon-submit file
    zincon_submit_path = os.path.join(tmp_dir, '.zincon-submit')
    with open(zincon_submit_path, 'w') as f:
        for file in skeleton_files:
            if (os.path.isfile(os.path.join(tmp_dir, file))):
                f.write(f"{file}\n")
        f.write("# Add additional files to submit here\n")

    # clean up temporary directory
    os.rename(tmp_dir, out)
    print(f"Initialized skeleton at {out}")
    
@cli.command()
@click.argument('path', required=True, type=click.Path(exists=True))
@click.option('--out', '-o', help="Output zip file path", default=None, type=click.Path())
def pack(path, out):   
    # Check if output directory exists, prompt for confirmation
    if out is None:
        out = os.path.join(path, 'submission.zip')
    if os.path.exists(out):
        click.confirm(f"The file {out} already exists. Do you want to overwrite it?", abort=True)
        shutil.rmtree(out)
    
    # Read .zincon-submit file
    zincon_submit_path = os.path.join(path, '.zincon-submit')
    files_to_pack = []
    if os.path.exists(zincon_submit_path):
        with open(zincon_submit_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    files_to_pack.append(line)
        with ZipFile(out, 'w') as zipf:
            for file in files_to_pack:
                file_path = os.path.join(path, file)
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=file)
                else:
                    click.echo(f"Warning: {file} listed in .zincon-submit not found in {path}. Skipping.")
    else:
        click.echo(f"No .zincon-submit file found in {path}. Packing all files.")
        shutil.make_archive(out, 'zip', path)

if __name__ == '__main__':
    cli()